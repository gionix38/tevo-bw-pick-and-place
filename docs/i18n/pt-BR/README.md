# Conversão da TEVO-BW em máquina pick-and-place

Projeto de engenharia para converter uma impressora 3D TEVO Black Widow em uma máquina de bancada para montagem de componentes SMT. O projeto inclui modelos paramétricos do FreeCAD, o alimentador TBW-Feeder v3.0, instruções de montagem, diagramas elétricos preliminares e listas de materiais (BOM).

> **Status:** projeto de protótipo. As verificações CAD e os diagramas não certificam uma máquina montada. Antes de operar, confira o encaixe na estrutura real, a fiação e as proteções, os limites de movimento e o desempenho do alimentador.

## Documentação principal

- [Dossiê ilustrado completo (PDF, 82 páginas)](../../../pnp/out/TEVO_BW_PnP_Dossier.pdf)
- [Guia de construção e montagem da máquina](../../../pnp/BUILD_AND_ASSEMBLY.md)
- [Relatório do modelo CAD atual](../../../pnp/out/report.md)
- [Arquitetura de alimentação e detalhes da fiação](../../../pnp/electronics/POWER_CONTROL_DESIGN.md)
- [Guia do alimentador TBW v3.0](../../../pnp/feeder/README.md)
- [BOM principal da máquina](../../../pnp/out/bom.csv)

## O que o projeto contém

- Modelo paramétrico da máquina para FreeCAD e scripts de geração.
- Estrutura mecânica, pórtico, cabeçote, mesa de trabalho e acionamentos.
- Alimentador de oito posições com avanço da fita e mecanismo de remoção da película de cobertura.
- Arquitetura preliminar de alimentação de 24 V, computador de controle, câmeras e controladores.
- Diagramas de montagem, renderizações, relatórios e BOMs preliminares.

## Gerar o CAD

Instale o FreeCAD 1.1. No PowerShell, execute:

```powershell
cd pnp
.\pnp.ps1 build
.\pnp.ps1 check
.\pnp.ps1 all
```

A verificação do modelo cobre posições definidas no CAD, mas não valida a estrutura física da impressora, a segurança elétrica nem o desempenho de produção. Para o OpenPnP, a recomendação atual é usar um computador x86-64; o Raspberry Pi está documentado como opção auxiliar/experimental até que o aplicativo ARM64 e as câmeras sejam validados.

Os documentos técnicos completos e o dossiê PDF ainda estão em inglês. Esta tradução é um resumo e um guia de navegação.

## Licença e arquivos de terceiros

O repositório ainda não tem uma licença geral definida. Algumas pastas contêm modelos CAD e imagens de terceiros com licenças próprias ou pouco claras. Verifique a origem e as licenças desses arquivos antes de redistribuir ou usar comercialmente.
