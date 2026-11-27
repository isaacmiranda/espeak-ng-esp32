<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Esqueleto do protocolo do estudo de escuta (rascunho, não submetido)

**Estado:** rascunho do assistente para o responsável revisar. Nada aqui foi submetido ao CEP, nenhum participante foi
contatado e nenhum dado foi coletado. Todo `[DECIDIR]` é decisão sua. Não há CAAE: a FR-LST-06 só libera a coleta com o
número do CAAE do protocolo aprovado registrado na FSD. O enquadramento (Res. CNS 466/2012 ou 510/2016) e os modelos
de documento são os do **CEP da sua instituição**: confirme com ele antes de redigir a versão final.

## 1. Pergunta e hipóteses

- **Pergunta:** a fala em português do Brasil do eSpeak NG no ESP32-S3 é inteligível para ouvintes, e como isso se compara
  entre ouvintes que enxergam e ouvintes cegos ou de baixa visão, para palavras comuns, frases sem sentido e nomes de
  fármacos?
- **Sem hipótese de resultado.** Nenhuma afirmação de inteligibilidade existe antes deste estudo. As estimativas por
  reconhecimento automático (whisper.cpp) são rotuladas como "estimativa por reconhecimento automático; não é medida de
  inteligibilidade com ouvintes" e não substituem o estudo.
- `[DECIDIR]` há hipóteses confirmatórias a pré-registrar (por exemplo, diferença entre grupos) ou o estudo é descritivo?

## 2. Desenho

- **Material** (já no repositório, `tests/corpus/listen/pt-br.tsv`): 200 palavras (lista Leipzig `por_news_2022_10K`,
  CC BY 4.0, rotulada "português (Leipzig), não específica de pt-BR"), 50 frases semanticamente imprevisíveis
  (Benoit et al., 1996; `tools/corpus/sus.py`) e 30 frases do dia a dia.
- `[DECIDIR]` incluir uma lista de **nomes de fármacos** (a lacuna que motiva o projeto; ver `docs/Ideia/spk-reference-drugs.md`):
  quais, e quem valida a grafia.
- **Condições:** `[DECIDIR]` quais vozes/ajustes comparar (padrão do eSpeak NG × ajustes de dicionário e velocidade) e se
  há uma referência (por exemplo um sintetizador de maior qualidade) para ancorar a escala.
- **Ordem:** quadrado latino por condição (FR-LST-02), gerado pela ferramenta; cada ouvinte recebe listas diferentes
  por condição, para espalhar o viés individual.
- **Medidas:** palavras corretas por item (taxa de erro de palavras) e `[DECIDIR]` nota de esforço/qualidade (MOS ou
  escala de esforço de escuta). Pontuação por dois avaliadores `[DECIDIR]` ou normalização automática com regras fixas.
- **Instrumento:** a ferramenta guiada de escuta (FR-LST-07..19), local, sem internet; as respostas ficam em arquivo
  sem identificação direta.

## 3. Participantes

- **Grupos** `[DECIDIR]`: ouvintes sem deficiência visual (controle); cegos; baixa visão. Audição: critério de triagem.
- **Tamanho** `[DECIDIR]`: número por grupo e justificativa (estudo exploratório × com poder estatístico).
- **Critérios de inclusão e exclusão** `[DECIDIR]`: idade, português do Brasil como língua principal, ausência de
  perda auditiva autorreferida, familiaridade com leitores de tela (registrar, não excluir).
- **Recrutamento** `[DECIDIR]`: por quais instituições ou associações; quem faz o contato. Sem contato antes da aprovação.
- **População potencialmente vulnerável:** tratar acessibilidade do consentimento (leitura em voz alta, formato
  acessível, possibilidade de assinar de outra forma) e do local.

## 4. Riscos, benefícios e segurança

- **Risco principal:** desconforto ou cansaço auditivo. Volume máximo fixado na bancada e ajuste inicial com frase de
  calibração (FR-LST-10); pausas; o ouvinte pode parar a qualquer momento sem justificar.
- **Benefício:** nenhum direto; o ganho é conhecimento sobre acessibilidade de fala embarcada em pt-BR.
- Nenhum aparelho é aplicado ao corpo; nenhum dado de saúde é coletado além do necessário para o grupo e a triagem
  auditiva autorreferida `[DECIDIR]`.

## 5. Dados, privacidade e LGPD

- **Nenhum dado identificável entra no git.** Respostas ficam com um código por participante; a tabela que liga o código
  à pessoa, se existir, fica fora do repositório, com acesso restrito `[DECIDIR]` (onde, por quanto tempo).
- Base legal e finalidade, tempo de guarda e descarte `[DECIDIR]`; compartilhamento de dados anonimizados `[DECIDIR]`.
- Áudio das respostas: `[DECIDIR]` gravar ou só registrar texto digitado (recomendo só registrar a resposta).

## 6. Consentimento

- TCLE com linguagem simples, versão acessível (leitor de tela e leitura em voz alta), contatos do pesquisador e do CEP,
  direito de desistir. A dispensa de TCLE, se for o caso, precisa de justificativa ao CEP.
- `[DECIDIR]` quem conduz a sessão e quem obtém o consentimento.

## 7. Análise

- Descritiva por grupo e condição; intervalos de confiança `[DECIDIR]` (método); comparação entre grupos só se o desenho
  permitir. O relatório separa o que foi medido do que não foi e repete a ressalva sobre o ASR.

## 8. Cronograma e pessoas

- `[DECIDIR]` pesquisador responsável, orientador/instituição proponente, CEP de destino (Plataforma Brasil), prazo
  (a aprovação costuma levar meses), local da coleta.

## 9. O que o assistente pode e não pode fazer daqui

- Pode: preparar o corpus, a ferramenta, os modelos de documento e a análise, e manter este esqueleto.
- Não pode: submeter, contatar participantes, ou afirmar qualquer resultado de inteligibilidade antes do estudo aprovado
  e concluído.
