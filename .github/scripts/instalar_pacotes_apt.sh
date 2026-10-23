#!/usr/bin/env bash
# Instala os pacotes do sistema da conversão de documentos com limite de tempo e
# nova tentativa (SPEC-0044). O espelho de pacotes do runner às vezes demora 15 a
# 30 minutos; cada tentativa é cancelada pelo limite e a seguinte recomeça limpa.
set -uo pipefail

LIMITE_SEGUNDOS="${APT_LIMITE_SEGUNDOS:-300}"
TENTATIVAS="${APT_TENTATIVAS:-3}"
PACOTES="tesseract-ocr tesseract-ocr-por libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress"

for tentativa in $(seq 1 "$TENTATIVAS"); do
  echo "Tentativa ${tentativa} de ${TENTATIVAS} do apt-get (limite de ${LIMITE_SEGUNDOS} s)"
  if sudo timeout --kill-after=10 "$LIMITE_SEGUNDOS" bash -c \
    "apt-get -o Acquire::Retries=3 update && apt-get -o Acquire::Retries=3 install -y --no-install-recommends ${PACOTES}"; then
    echo "Pacotes do sistema instalados na tentativa ${tentativa}."
    exit 0
  fi
  echo "Tentativa ${tentativa} falhou ou passou do limite; reconfigurando o dpkg antes da próxima."
  sudo dpkg --configure -a || true
done

echo "ERRO: a instalação dos pacotes do sistema falhou após ${TENTATIVAS} tentativas." >&2
exit 1
