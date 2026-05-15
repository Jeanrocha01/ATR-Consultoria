#!/usr/bin/env python3
"""Gera arquivos R11 (Livro de Apuração de Entrada PER/DCOMP) separados por trimestre.

Layout (linha de 112 caracteres + CRLF):
  01 Tipo                              R11                (3)
  02 CNPJ Declarante                   14 dígitos
  03 CNPJ Sucedida                     14 dígitos (ou 14 espaços)
  04 CNPJ Detentor do Crédito          14 dígitos
  05 Ano de Apuração (AAAA)            4
  06 Mês de Apuração (MM)              2
  07 Forma de Apuração                 1 ("0" = mensal)
  08 CFOP                              4
  09 Valor Base de Cálculo             14 (centavos, zero à esquerda)
  10 Valor IPI Creditado               14
  11 Valor Isentas/Não Tributadas      14
  12 Valor Outras                      14
  13 EOL (CRLF)
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORIGEM = BASE / "dados.tsv"
SAIDA = BASE / "trimestres"


def valor_para_centavos(valor: str) -> str:
    """Converte '5267,64' -> '00000000526764' (14 dígitos, centavos)."""
    v = (valor or "").strip().replace(".", "").replace(" ", "")
    if not v:
        v = "0"
    if "," in v:
        inteiro, dec = v.split(",", 1)
    else:
        inteiro, dec = v, "0"
    dec = (dec + "00")[:2]
    inteiro = inteiro.lstrip("0") or "0"
    centavos = int(inteiro) * 100 + int(dec)
    return f"{centavos:014d}"


def cnpj_normaliza(valor: str) -> str:
    so_digitos = "".join(ch for ch in (valor or "") if ch.isdigit())
    if not so_digitos:
        return " " * 14
    return so_digitos.zfill(14)


def trimestre(mes: int) -> int:
    return (mes - 1) // 3 + 1


def monta_linha(row: dict) -> str:
    tipo = row["Tipo"].strip()
    decl = cnpj_normaliza(row["CNPJ Declarante"])
    suc = cnpj_normaliza(row["CNPJ Sucedida"])
    det = cnpj_normaliza(row["CNPJ Detentor Crédito"])
    ano = row["Ano Período"].strip().zfill(4)
    mes = row["Mês Período"].strip().zfill(2)
    forma = (row["Período Apuração"].strip() or "0")[:1]
    cfop = row["CFOP"].strip().zfill(4)
    base = valor_para_centavos(row["Vlr Base Cálculo"])
    ipi = valor_para_centavos(row["Vlr IPI"])
    isentas = valor_para_centavos(row["Vlr Isentas/Não Tributadas"])
    outras = valor_para_centavos(row["Vlr Outros"])
    linha = f"{tipo}{decl}{suc}{det}{ano}{mes}{forma}{cfop}{base}{ipi}{isentas}{outras}"
    assert len(linha) == 112, f"Linha com tamanho inválido ({len(linha)}): {linha!r}"
    return linha


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)

    grupos: dict[tuple[int, int], list[str]] = defaultdict(list)

    with ORIGEM.open(newline="", encoding="utf-8") as fh:
        leitor = csv.DictReader(fh, delimiter="\t")
        for row in leitor:
            ano = int(row["Ano Período"])
            mes = int(row["Mês Período"])
            grupos[(ano, trimestre(mes))].append(monta_linha(row))

    resumo: list[str] = []
    for (ano, trim), linhas in sorted(grupos.items()):
        nome = f"R11_{ano}_{trim}T.txt"
        destino = SAIDA / nome
        with destino.open("w", encoding="latin-1", newline="") as out:
            out.write("\r\n".join(linhas) + "\r\n")
        resumo.append(f"{nome}: {len(linhas)} registros")

    for item in resumo:
        print(item)


if __name__ == "__main__":
    main()
