// SPDX-License-Identifier: GPL-3.0-or-later
// Data partition (FSD §12, Appendix A) -> read-only VFS. Files are read straight from the
// flash mapping; the upstream engine copies what it needs with malloc (FR-MEM-04).
#include "espk_part.h"

#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>

#include "esp_partition.h"
#include "esp_rom_crc.h"
#include "esp_vfs.h"

#define MAGIC "ESPK"
#define FORMAT 1u
#define HEADER_LEN 36u
#define MAX_FD 4

typedef struct __attribute__((packed)) {
    char magic[4];
    uint16_t format, flags;
    char espeak_version[16];
    uint32_t count, payload_size, crc32;
} header_t;

static const espk_entry_t *s_tab;
static uint32_t s_count;
static const uint8_t *s_payload;
static esp_partition_mmap_handle_t s_map;

static struct {
    const espk_entry_t *e;
    uint32_t pos;
} s_fd[MAX_FD];

const espk_entry_t *espk_part_entry(uint32_t i) { return i < s_count ? &s_tab[i] : NULL; }

static const espk_entry_t *find(const char *path)
{
    while (*path == '/') path++;
    for (uint32_t i = 0; i < s_count; i++)
        if (strncmp(s_tab[i].name, path, sizeof s_tab[i].name) == 0) return &s_tab[i];
    return NULL;
}

// "", "/" and every directory prefix of a table entry are directories.
static bool is_dir(const char *path)
{
    while (*path == '/') path++;
    size_t n = strlen(path);
    while (n && path[n - 1] == '/') n--;
    if (n == 0) return true;
    for (uint32_t i = 0; i < s_count; i++)
        if (strncmp(s_tab[i].name, path, n) == 0 && s_tab[i].name[n] == '/') return true;
    return false;
}

static int vfs_open(const char *path, int flags, int mode)
{
    (void)mode;
    if ((flags & O_ACCMODE) != O_RDONLY || (flags & O_CREAT)) {
        errno = EROFS;
        return -1;
    }
    const espk_entry_t *e = find(path);
    if (!e) {
        errno = is_dir(path) ? EISDIR : ENOENT;
        return -1;
    }
    for (int fd = 0; fd < MAX_FD; fd++) {
        if (!s_fd[fd].e) {
            s_fd[fd].e = e;
            s_fd[fd].pos = 0;
            return fd;
        }
    }
    errno = ENFILE;
    return -1;
}

static bool fd_ok(int fd) { return fd >= 0 && fd < MAX_FD && s_fd[fd].e; }

static ssize_t vfs_read(int fd, void *dst, size_t size)
{
    if (!fd_ok(fd)) {
        errno = EBADF;
        return -1;
    }
    uint32_t left = s_fd[fd].e->size - s_fd[fd].pos;
    if (size > left) size = left;
    memcpy(dst, s_payload + s_fd[fd].e->offset + s_fd[fd].pos, size);
    s_fd[fd].pos += size;
    return (ssize_t)size;
}

static ssize_t vfs_write(int fd, const void *src, size_t size)
{
    (void)fd, (void)src, (void)size;
    errno = EROFS;
    return -1;
}

static off_t vfs_lseek(int fd, off_t off, int whence)
{
    if (!fd_ok(fd)) {
        errno = EBADF;
        return -1;
    }
    off_t base = whence == SEEK_SET ? 0
               : whence == SEEK_CUR ? (off_t)s_fd[fd].pos
               : whence == SEEK_END ? (off_t)s_fd[fd].e->size
                                    : -1;
    off_t p = base + off;
    if (base < 0 || p < 0 || p > (off_t)s_fd[fd].e->size) {
        errno = EINVAL;
        return -1;
    }
    s_fd[fd].pos = (uint32_t)p;
    return p;
}

static int vfs_close(int fd)
{
    if (!fd_ok(fd)) {
        errno = EBADF;
        return -1;
    }
    s_fd[fd].e = NULL;
    return 0;
}

static void fill_stat(struct stat *st, const espk_entry_t *e)
{
    memset(st, 0, sizeof *st);
    st->st_mode = e ? (S_IFREG | 0444) : (S_IFDIR | 0555);
    st->st_size = e ? (off_t)e->size : 0;
}

static int vfs_fstat(int fd, struct stat *st)
{
    if (!fd_ok(fd)) {
        errno = EBADF;
        return -1;
    }
    fill_stat(st, s_fd[fd].e);
    return 0;
}

static int vfs_stat(const char *path, struct stat *st)
{
    const espk_entry_t *e = find(path);
    if (!e && !is_dir(path)) {
        errno = ENOENT;
        return -1;
    }
    fill_stat(st, e);
    return 0;
}

esp_err_t espk_part_mount(const char *label, uint8_t subtype, const char *base, const char *engine_version,
                          const char **reason)
{
    const esp_partition_t *p =
        esp_partition_find_first(ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)subtype, label);
    if (!p) {
        *reason = "no_partition";
        return ESP_ERR_NOT_FOUND;
    }
    const void *map;
    esp_err_t err = esp_partition_mmap(p, 0, p->size, ESP_PARTITION_MMAP_DATA, &map, &s_map);
    if (err != ESP_OK) {
        *reason = "mmap";
        return err;
    }
    const uint8_t *b = map;
    header_t h;
    memcpy(&h, b, sizeof h);
    err = ESP_ERR_INVALID_CRC;
    if (memcmp(h.magic, MAGIC, 4) != 0 || h.format != FORMAT) {
        *reason = "bad_magic";
        goto fail;
    }
    uint64_t body = (uint64_t)h.count * sizeof(espk_entry_t) + h.payload_size;
    if (body > p->size - HEADER_LEN || esp_rom_crc32_le(0, b + HEADER_LEN, (uint32_t)body) != h.crc32) {
        *reason = "bad_crc";
        goto fail;
    }
    if (strncmp(h.espeak_version, engine_version, sizeof h.espeak_version) != 0) {
        *reason = "bad_version";
        err = ESP_ERR_INVALID_VERSION;
        goto fail;
    }
    s_tab = (const espk_entry_t *)(b + HEADER_LEN);
    s_count = h.count;
    s_payload = b + HEADER_LEN + h.count * sizeof(espk_entry_t);
    for (uint32_t i = 0; i < s_count; i++) {
        if (s_tab[i].name[sizeof s_tab[i].name - 1] != '\0' ||
            (uint64_t)s_tab[i].offset + s_tab[i].size > h.payload_size) {
            *reason = "bad_table";  // a valid CRC over an incoherent table: a broken generator
            goto fail;
        }
    }
    static const esp_vfs_t vfs = {
        .flags = ESP_VFS_FLAG_DEFAULT,
        .open = vfs_open,
        .read = vfs_read,
        .write = vfs_write,
        .lseek = vfs_lseek,
        .close = vfs_close,
        .fstat = vfs_fstat,
        .stat = vfs_stat,
    };
    err = esp_vfs_register(base, &vfs, NULL);
    if (err != ESP_OK) {
        *reason = "vfs";
        goto fail;
    }
    return ESP_OK;
fail:
    esp_partition_munmap(s_map);
    s_count = 0;
    s_tab = NULL;
    return err;
}

uint32_t espk_part_count(void) { return s_count; }
