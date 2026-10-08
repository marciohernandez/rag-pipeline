#!/usr/bin/env bash
# Provisionamento, conferência e troca dos secrets de produção do Swarm (SPEC-0027).
#
# Os valores nunca passam por argumento, histórico do shell, arquivo ou log: entram
# no `docker secret create` somente pela entrada padrão. Ver deploy/SECRETS.md.

set -euo pipefail

NOMES=(openrouter_api_key r2_credentials postgres_password conexoes_chave)
AMBIENTE="producao"
ENTRADA_PADRAO=0
CONFIRMAR=0

usar() {
  cat <<'AJUDA'
Uso: deploy/secrets.sh <subcomando> [nome...] [parâmetros]

Subcomandos:
  criar [nome...]     Cria os secrets ausentes (versão 1). Sem nomes, completa só os que
                      faltam; com nome explícito, recusa o que já existe.
  trocar <nome>       Cria a próxima versão de um secret e preserva a anterior.
  verificar           Falha, listando os ausentes, se algum secret não existir.
  resolver            Imprime VARIAVEL=nome_do_secret com a versão mais alta de cada um.

Parâmetros:
  --ambiente producao|local   Ambiente (padrão: producao). O local usa o sufixo _local e
                              valores fictícios, sem perguntas.
  --confirmar-consequencia    Autoriza a troca de postgres_password e conexoes_chave.
  --entrada-padrao            Lê os valores pedidos como linhas da entrada padrão
                              (automação e testes); sem ele, exige um terminal.
  --ajuda                     Mostra esta ajuda.

Secrets: openrouter_api_key, r2_credentials, postgres_password, conexoes_chave.
Nomes no Swarm: <nome>_v<N> (produção) e <nome>_local_v<N> (local).
Saídas: 0 sucesso; 1 uso, validação ou secret ausente; 2 sem Docker ou fora do manager.
AJUDA
}

erro() { echo "ERRO: $*" >&2; }
info() { echo "$*"; }

sufixo() {
  if [ "$AMBIENTE" = "local" ]; then echo "_local"; fi
}

variavel_de() {
  case "$1" in
    openrouter_api_key) echo "OPENROUTER_API_KEY_SECRET" ;;
    r2_credentials) echo "R2_CREDENTIALS_SECRET" ;;
    postgres_password) echo "POSTGRES_PASSWORD_SECRET" ;;
    conexoes_chave) echo "CONEXOES_CHAVE_SECRET" ;;
  esac
}

nome_conhecido() {
  local candidato
  for candidato in "${NOMES[@]}"; do
    [ "$candidato" = "$1" ] && return 0
  done
  return 1
}

exigir_docker() {
  if ! command -v docker > /dev/null 2>&1; then
    erro "Docker não encontrado no PATH. Execute este script no servidor com a CLI do Docker."
    exit 2
  fi
  local gerenciador
  gerenciador="$(docker info --format '{{.Swarm.ControlAvailable}}' 2> /dev/null || true)"
  if [ "$gerenciador" != "true" ]; then
    erro "Este nó não é manager do Swarm. Execute o script em um nó manager."
    exit 2
  fi
}

listar_secrets() {
  docker secret ls --format '{{.Name}}' 2> /dev/null || true
}

# versao_atual <nome>: maior N entre os secrets <nome>[_local]_v<N>; vazio se não houver.
versao_atual() {
  local nome="$1" maior="" linha
  local padrao="^${nome}$(sufixo)_v([0-9]+)$"
  while IFS= read -r linha; do
    if [[ "$linha" =~ $padrao ]]; then
      local numero="${BASH_REMATCH[1]}"
      if [ -z "$maior" ] || [ "$numero" -gt "$maior" ]; then
        maior="$numero"
      fi
    fi
  done < <(listar_secrets)
  echo "$maior"
}

# ---- leitura de valores ----------------------------------------------------

LIDO=""
ler_valor() {
  # ler_valor <pergunta> ; devolve em LIDO sem eco e sem aceitar valor por argumento
  local pergunta="$1"
  LIDO=""
  if [ "$ENTRADA_PADRAO" = "1" ]; then
    IFS= read -r LIDO || LIDO=""
  elif [ -t 0 ]; then
    IFS= read -r -s -p "$pergunta: " LIDO || LIDO=""
    echo >&2
  else
    erro "Entrada não interativa. Execute em um terminal (ou use --entrada-padrao em automação)."
    exit 1
  fi
}

gerar_senha() {
  local senha=""
  while [ "${#senha}" -lt 32 ]; do
    senha="$(openssl rand -base64 64 | LC_ALL=C tr -dc 'A-Za-z0-9' | head -c 32 || true)"
  done
  echo "$senha"
}

gerar_chave_fernet() {
  openssl rand -base64 32 | tr '+/' '-_'
}

# citar <valor>: sem aspas quando seguro para `. arquivo`, com aspas simples caso contrário.
citar() {
  local valor="$1"
  if [[ "$valor" =~ ^[A-Za-z0-9._:/@+=,-]+$ ]]; then
    printf '%s' "$valor"
  else
    printf "'%s'" "${valor//\'/\'\\\'\'}"
  fi
}

# ---- criação ----------------------------------------------------------------

# criar_secret <nome_completo> <valor> ; o valor vai somente pela entrada padrão
criar_secret() {
  local nome_completo="$1" valor="$2"
  if ! printf '%s' "$valor" | docker secret create "$nome_completo" - > /dev/null; then
    return 1
  fi
}

declare -A VALORES_PREPARADOS=()
declare -A GERADOS=()

# preparar_valor <nome>: obtém e valida o valor sem criar nada
preparar_valor() {
  local nome="$1"
  case "$nome" in
    openrouter_api_key)
      if [ "$AMBIENTE" = "local" ]; then
        VALORES_PREPARADOS[$nome]="chave-ficticia-ensaio-local"
        return 0
      fi
      ler_valor "Chave da OpenRouter"
      [ -n "$LIDO" ] || { erro "Informe a chave da OpenRouter."; exit 1; }
      VALORES_PREPARADOS[$nome]="$LIDO"
      ;;
    r2_credentials)
      if [ "$AMBIENTE" = "local" ]; then
        VALORES_PREPARADOS[$nome]="# ensaio local: sem credenciais do R2, uploads gravados em disco"
        return 0
      fi
      local bucket endpoint acesso segredo
      ler_valor "Bucket do R2"; bucket="$LIDO"
      [ -n "$bucket" ] || { erro "Informe o bucket do R2."; exit 1; }
      ler_valor "Endpoint do R2 (http:// ou https://)"; endpoint="$LIDO"
      [[ "$endpoint" =~ ^https?://[^[:space:]]+$ ]] || {
        erro "O endpoint do R2 deve começar com http:// ou https://."
        exit 1
      }
      ler_valor "Access key do R2"; acesso="$LIDO"
      [ -n "$acesso" ] || { erro "Informe a access key do R2."; exit 1; }
      ler_valor "Secret key do R2"; segredo="$LIDO"
      [ -n "$segredo" ] || { erro "Informe a secret key do R2."; exit 1; }
      VALORES_PREPARADOS[$nome]="APP_R2_BUCKET=$(citar "$bucket")
APP_R2_ENDPOINT_URL=$(citar "$endpoint")
APP_R2_ACCESS_KEY_ID=$(citar "$acesso")
APP_R2_SECRET_ACCESS_KEY=$(citar "$segredo")"
      ;;
    postgres_password)
      VALORES_PREPARADOS[$nome]="$(gerar_senha)"
      GERADOS[$nome]=1
      ;;
    conexoes_chave)
      VALORES_PREPARADOS[$nome]="$(gerar_chave_fernet)"
      GERADOS[$nome]=1
      ;;
  esac
}

# gravar_versao <nome> <versao>: cria <nome>[_local]_v<versao> e exibe o valor se gerado
gravar_versao() {
  local nome="$1" versao="$2"
  local completo="${nome}$(sufixo)_v${versao}"
  if ! criar_secret "$completo" "${VALORES_PREPARADOS[$nome]}"; then
    erro "Não foi possível criar ${completo}."
    return 1
  fi
  info "Criado: ${completo}"
  if [ "${GERADOS[$nome]:-0}" = "1" ] && [ "$AMBIENTE" != "local" ]; then
    echo "VALOR GERADO ${completo}: ${VALORES_PREPARADOS[$nome]}"
    echo "Guarde este valor agora no gerenciador de senhas: ele não será exibido de novo."
  fi
}

cmd_criar() {
  local pedidos=("$@") alvo=() nome atual
  if [ "${#pedidos[@]}" -gt 0 ]; then
    for nome in "${pedidos[@]}"; do
      nome_conhecido "$nome" || { erro "Secret desconhecido: ${nome}."; exit 1; }
    done
    for nome in "${pedidos[@]}"; do
      atual="$(versao_atual "$nome")"
      if [ -n "$atual" ]; then
        erro "O secret ${nome} já existe (${nome}$(sufixo)_v${atual}). Use 'deploy/secrets.sh trocar ${nome}' para criar a próxima versão."
        exit 1
      fi
      alvo+=("$nome")
    done
  else
    for nome in "${NOMES[@]}"; do
      atual="$(versao_atual "$nome")"
      if [ -n "$atual" ]; then
        info "Secret ${nome}$(sufixo)_v${atual} já existe e foi preservado."
      else
        alvo+=("$nome")
      fi
    done
  fi
  if [ "${#alvo[@]}" -eq 0 ]; then
    info "Nada a criar: todos os secrets já existem."
    return 0
  fi
  # valida tudo antes de criar qualquer secret
  for nome in "${alvo[@]}"; do
    preparar_valor "$nome"
  done
  for nome in "${alvo[@]}"; do
    gravar_versao "$nome" 1 || exit 1
  done
}

# ---- troca --------------------------------------------------------------------

consequencia_de() {
  case "$1" in
    postgres_password)
      echo "Trocar postgres_password só no Swarm derruba backend e worker: o Postgres não relê o secret depois que o banco existe."
      echo "Antes do deploy, altere a senha dentro do banco com o novo valor, por exemplo:"
      echo "  docker exec -it \$(docker ps -q -f name=postgres_ragpipeline) psql -U rag_pipeline -d rag_pipeline -c \"ALTER USER rag_pipeline PASSWORD '<novo valor>'\""
      ;;
    conexoes_chave)
      echo "Trocar conexoes_chave torna ilegíveis as chaves de todas as conexões cadastradas."
      echo "Depois do deploy, será preciso recadastrar a chave de cada conexão em Conexões."
      ;;
  esac
}

cmd_trocar() {
  [ "$#" -eq 1 ] || { erro "Informe o secret a trocar: deploy/secrets.sh trocar <nome>."; exit 1; }
  local nome="$1" atual proxima
  nome_conhecido "$nome" || { erro "Secret desconhecido: ${nome}."; exit 1; }
  atual="$(versao_atual "$nome")"
  [ -n "$atual" ] || { erro "O secret ${nome} ainda não existe. Use 'deploy/secrets.sh criar ${nome}'."; exit 1; }
  proxima=$((atual + 1))

  if [ "$nome" = "postgres_password" ] || [ "$nome" = "conexoes_chave" ]; then
    if [ "$CONFIRMAR" != "1" ]; then
      erro "A troca de ${nome} tem efeito colateral e está bloqueada por padrão."
      consequencia_de "$nome" >&2
      echo "Para continuar, repita com --confirmar-consequencia." >&2
      exit 1
    fi
    consequencia_de "$nome"
    ler_valor "Digite o nome do secret (${nome}) para confirmar"
    if [ "$LIDO" != "$nome" ]; then
      erro "Confirmação incorreta. Nada foi criado."
      exit 1
    fi
  fi

  preparar_valor "$nome"
  if ! gravar_versao "$nome" "$proxima"; then
    erro "A versão ${nome}$(sufixo)_v${atual} continua vigente; nada foi removido."
    exit 1
  fi
  info "A versão anterior (${nome}$(sufixo)_v${atual}) foi preservada."
  info "O próximo deploy aplica a nova versão em atualização controlada pelo Swarm."
}

# ---- verificação e resolução --------------------------------------------------

cmd_verificar() {
  local ausentes=() nome
  for nome in "${NOMES[@]}"; do
    [ -n "$(versao_atual "$nome")" ] || ausentes+=("$nome")
  done
  if [ "${#ausentes[@]}" -gt 0 ]; then
    local opcao=""
    [ "$AMBIENTE" = "local" ] && opcao=" --ambiente local"
    erro "Faltam secrets no Swarm:"
    for nome in "${ausentes[@]}"; do
      echo "  - ${nome} -> deploy/secrets.sh criar ${nome}${opcao}" >&2
    done
    exit 1
  fi
  info "Todos os secrets existem."
}

cmd_resolver() {
  local nome versao
  for nome in "${NOMES[@]}"; do
    versao="$(versao_atual "$nome")"
    if [ -n "$versao" ]; then
      echo "$(variavel_de "$nome")=${nome}$(sufixo)_v${versao}"
    fi
  done
}

# ---- despacho -----------------------------------------------------------------

SUBCOMANDO=""
ARGUMENTOS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --ajuda | -h) usar; exit 0 ;;
    --entrada-padrao) ENTRADA_PADRAO=1 ;;
    --confirmar-consequencia) CONFIRMAR=1 ;;
    --ambiente)
      shift
      [ "$#" -gt 0 ] || { erro "Informe o ambiente: producao ou local."; exit 1; }
      case "$1" in
        producao | local) AMBIENTE="$1" ;;
        *) erro "Ambiente inválido: use producao ou local."; exit 1 ;;
      esac
      ;;
    -*) erro "Parâmetro desconhecido: $1."; usar >&2; exit 1 ;;
    *)
      if [ -z "$SUBCOMANDO" ]; then SUBCOMANDO="$1"; else ARGUMENTOS+=("$1"); fi
      ;;
  esac
  shift
done

[ -n "$SUBCOMANDO" ] || { usar >&2; exit 1; }

case "$SUBCOMANDO" in
  criar | trocar | verificar | resolver) ;;
  *) erro "Subcomando desconhecido: ${SUBCOMANDO}."; usar >&2; exit 1 ;;
esac

exigir_docker

case "$SUBCOMANDO" in
  criar) cmd_criar "${ARGUMENTOS[@]+"${ARGUMENTOS[@]}"}" ;;
  trocar) cmd_trocar "${ARGUMENTOS[@]+"${ARGUMENTOS[@]}"}" ;;
  verificar) cmd_verificar ;;
  resolver) cmd_resolver ;;
esac
