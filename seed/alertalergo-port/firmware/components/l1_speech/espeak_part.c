/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Partição `espeak` (FR-PLT-06) → VFS somente leitura em /es. Os arquivos são
 * lidos direto do mapeamento da flash; o eSpeak os copia para a heap (PSRAM,
 * acima de CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL).
 */
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>

#include "esp_partition.h"
#include "esp_rom_crc.h"
#include "esp_vfs.h"
#include "espeak_part.h"

#define MAGIC "AAES"
#define FORMAT 1u
#define NAME_LEN 32
#define MAX_FD 4

typedef struct __attribute__((packed)) {
    char name[NAME_LEN];
    uint32_t off, len;          /* off a partir do byte 16 */
} entry_t;

static const uint8_t *s_body;   /* byte 16 da partição */
static const entry_t *s_tab;
static uint32_t s_count;

static struct {
    const entry_t *e;
    uint32_t pos;
} s_fd[MAX_FD];

static const entry_t *find(const char *path)
{
    while (*path == '/') path++;
    for (uint32_t i = 0; i < s_count; i++)
        if (strncmp(s_tab[i].name, path, NAME_LEN) == 0) return &s_tab[i];
    return NULL;
}

/* "", "/" e todo prefixo de diretório de um arquivo da tabela são diretórios. */
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
    if ((flags & O_ACCMODE) != O_RDONLY) { errno = EROFS; return -1; }
    const entry_t *e = find(path);
    if (!e) { errno = is_dir(path) ? EISDIR : ENOENT; return -1; }
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
    if (!fd_ok(fd)) { errno = EBADF; return -1; }
    uint32_t left = s_fd[fd].e->len - s_fd[fd].pos;
    if (size > left) size = left;
    memcpy(dst, s_body + s_fd[fd].e->off + s_fd[fd].pos, size);
    s_fd[fd].pos += size;
    return (ssize_t)size;
}

static off_t vfs_lseek(int fd, off_t off, int whence)
{
    if (!fd_ok(fd)) { errno = EBADF; return -1; }
    off_t base = whence == SEEK_SET ? 0 : whence == SEEK_CUR ? (off_t)s_fd[fd].pos
               : whence == SEEK_END ? (off_t)s_fd[fd].e->len : -1;
    off_t p = base + off;
    if (base < 0 || p < 0 || p > (off_t)s_fd[fd].e->len) { errno = EINVAL; return -1; }
    s_fd[fd].pos = (uint32_t)p;
    return p;
}

static int vfs_close(int fd)
{
    if (!fd_ok(fd)) { errno = EBADF; return -1; }
    s_fd[fd].e = NULL;
    return 0;
}

static void fill_stat(struct stat *st, const entry_t *e)
{
    memset(st, 0, sizeof *st);
    st->st_mode = e ? (S_IFREG | 0444) : (S_IFDIR | 0555);
    st->st_size = e ? (off_t)e->len : 0;
}

static int vfs_fstat(int fd, struct stat *st)
{
    if (!fd_ok(fd)) { errno = EBADF; return -1; }
    fill_stat(st, s_fd[fd].e);
    return 0;
}

static int vfs_stat(const char *path, struct stat *st)
{
    const entry_t *e = find(path);
    if (!e && !is_dir(path)) { errno = ENOENT; return -1; }
    fill_stat(st, e);
    return 0;
}

esp_err_t espeak_part_mount(const char *base, const char **reason)
{
    const esp_partition_t *p = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, 0x40, "espeak");
    if (!p) { *reason = "no_partition"; return ESP_ERR_NOT_FOUND; }
    const void *map;
    esp_partition_mmap_handle_t h;
    esp_err_t err = esp_partition_mmap(p, 0, p->size, ESP_PARTITION_MMAP_DATA, &map, &h);
    if (err != ESP_OK) { *reason = "mmap"; return err; }
    const uint8_t *b = map;
    uint32_t hdr[4];
    memcpy(hdr, b, sizeof hdr);
    if (memcmp(b, MAGIC, 4) != 0) { *reason = "bad_magic"; goto fail; }
    if (hdr[1] != FORMAT) { *reason = "bad_version"; goto fail; }
    uint32_t size = hdr[2];
    if (size < 4 || size > p->size - 16 || esp_rom_crc32_le(0, b + 16, size) != hdr[3]) {
        *reason = "bad_crc";
        goto fail;
    }
    memcpy(&s_count, b + 16, 4);
    if ((uint64_t)4 + (uint64_t)s_count * sizeof(entry_t) > size) { *reason = "bad_crc"; goto fail; }
    s_body = b + 16;
    s_tab = (const entry_t *)(b + 20);
    for (uint32_t i = 0; i < s_count; i++) {
        if (s_tab[i].name[NAME_LEN - 1] != '\0' || (uint64_t)s_tab[i].off + s_tab[i].len > size) {
            *reason = "bad_crc";      /* tabela incoerente com CRC válido: imagem mal gerada */
            goto fail;
        }
    }
    static const esp_vfs_t vfs = {
        .flags = ESP_VFS_FLAG_DEFAULT | ESP_VFS_FLAG_READONLY_FS,
        .open = vfs_open, .read = vfs_read, .lseek = vfs_lseek, .close = vfs_close,
        .fstat = vfs_fstat, .stat = vfs_stat,
    };
    err = esp_vfs_register(base, &vfs, NULL);
    if (err != ESP_OK) { *reason = "vfs"; return err; }
    return ESP_OK;
fail:
    esp_partition_munmap(h);
    s_count = 0;
    return ESP_ERR_INVALID_CRC;
}
