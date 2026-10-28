# Validação — ChimpiBridge 0.1.1 para Windows e macOS

Data: 28/10/2026

A Release pública foi criada e publicada pela conta **Chimpi-hackintosh**
O campo nativo de publicador do GitHub foi conferido, além do título e dos créditos

[Release publicada com os quatro pacotes](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases/tag/v0.1.1)

## Pacotes e testes reais

| Sistema | Testes automatizados | Execução do aplicativo compilado |
|---|---|---|
| Windows 2025 x64 | 50 aprovados | EXE da pasta portátil e EXE independente abertos e renderizados |
| macOS 15 Apple Silicon | 50 aprovados | App aberto antes e depois de extrair o ZIP |
| macOS 15 Intel | 50 aprovados | App aberto antes e depois de extrair o ZIP |

[Job Windows aprovado](https://github.com/Chimpi-hackintosh/ChimpiBridge/actions/runs/40768442381/job/123098898548)

[Job macOS Apple Silicon aprovado](https://github.com/Chimpi-hackintosh/ChimpiBridge/actions/runs/40768442381/job/123098898579)

[Job macOS Intel aprovado](https://github.com/Chimpi-hackintosh/ChimpiBridge/actions/runs/40768442381/job/123098898587)

[Preparação final da publicação aprovada](https://github.com/Chimpi-hackintosh/ChimpiBridge/actions/runs/40769473552)

Os pacotes foram compilados a partir da revisão `d49e25db0004e604097ed92ccfa35d13de41547f`
A tag inclui também o ajuste posterior do fluxo de publicação, sem alteração do código do aplicativo

## Integridade dos anexos

| Pacote | Bytes | SHA-256 |
|---|---:|---|
| ChimpiBridge-0.1.1-windows-x64-portable.zip | 49467214 | 5c6c824bc2aa7a2a2a66cea32677e6e5dc2894d0cc547679523217154232c4eb |
| ChimpiBridge-0.1.1-windows-x64.exe | 41349396 | a8afccbcb39701c2290443fec9ddbdfaec3fa05df67ef041d1f3436407f292ff |
| ChimpiBridge-0.1.1-macos-arm64.zip | 44660242 | 6d933338e478f78a6513da4c6767cb06c5c6a885adc882f31278bda541fe8344 |
| ChimpiBridge-0.1.1-macos-x64.zip | 47217493 | 7aa81f69ebd3ad6de4d16c1dc8a767c8bb07c67d8df46cffec9406608db3cf0b |

Cada pacote tem seu arquivo `.sha256` separado na Release
Os tamanhos e hashes foram conferidos novamente após publicar

## O que foi executado

- Inicialização dos executáveis a partir de outro diretório de trabalho, removendo PYTHONPATH, PYTHONHOME e VIRTUAL_ENV do ambiente de teste
- Renderização offscreen da janela e do ícone SVG
- Execução real de `adb version` pela ferramenta incluída nos pacotes completos
- Download real do Google, SHA-256, extração e execução do ADB dentro do runtime do EXE independente Windows
- Verificação estrutural das assinaturas ad hoc dos apps macOS, antes e depois de extrair os ZIPs
- Reabertura dos apps extraídos para conferir permissões, symlinks, recursos e bibliotecas
- Ausência de fontes `.py` e `.pyw` nas distribuições completas
- Verificações de autoria da Release e de recuperação da publicação anterior em caso de falha

A versão automática anterior foi preservada como rascunho de backup, com os arquivos originais e a revisão de origem registrados
Nenhuma publicação anterior precisou ser apagada permanentemente para trocar o publicador

## Limites da verificação

A comunicação USB e a troca de modos em celulares físicos ainda não foram testadas
Os testes de aparelho utilizam adaptadores simulados
Um computador limpo de usuário final ainda precisa ser validado fora dos runners
Os apps macOS exigem macOS 14.4 ou posterior e têm assinatura ad hoc local, sem notarização Apple
O setup instalável Windows não foi compilado; ele continua a cargo de Chimpi-hackintosh
Download Mode, Fastboot e o backend iPhone permanecem planejados
