# ChimpiBridge 0.1.1 — Windows e macOS

**Autor, mantenedor e publicador: [Chimpi-hackintosh](https://github.com/Chimpi-hackintosh)**

## Downloads

| Arquivo | Uso |
|---|---|
| ChimpiBridge-0.1.1-windows-x64-portable.zip | Pasta completa com EXE, runtime, bibliotecas e ADB incluído |
| ChimpiBridge-0.1.1-windows-x64.exe | EXE independente, sem instalar Python; prepara o ADB automaticamente quando necessário |
| ChimpiBridge-0.1.1-macos-arm64.zip | ChimpiBridge.app para Mac com Apple Silicon |
| ChimpiBridge-0.1.1-macos-x64.zip | ChimpiBridge.app para Mac com processador Intel |

Cada pacote tem seu arquivo SHA-256
No Windows portátil, extraia e mantenha a pasta inteira
O EXE independente precisa de internet na primeira preparação automática do ADB quando não há ferramenta disponível
No macOS, extraia o ZIP e mova ChimpiBridge.app para Aplicativos
As versões macOS incluem runtime, bibliotecas e ferramentas ADB, exigem macOS 14.4 ou posterior e usam assinatura ad hoc local, sem notarização Apple

O setup instalável do Windows é preparado separadamente por Chimpi-hackintosh

## Funcionalidades

- Detectar e selecionar Android por ADB
- Reiniciar o Android ou entrar no Recovery já instalado
- Preparar o ADB oficial em segundo plano no Windows quando ele está ausente, conferindo o SHA-256 antes da execução
- Acompanhar a reconexão e confirmar o modo quando há evidência do mesmo aparelho
- Interface em português e inglês e histórico local

## Verificação

Testes de núcleo e interface executados em Windows, macOS Apple Silicon e macOS Intel
Executáveis compilados abertos e renderizados nos respectivos sistemas
O app macOS também é extraído do ZIP e aberto novamente para conferir permissões, symlinks e recursos
O EXE independente do Windows é aberto a partir de outra pasta e testa o download real do ADB no runtime empacotado

A comunicação USB e a troca de modos em aparelhos físicos ainda precisam de validação
Download Mode, Fastboot e o backend iPhone continuam planejados

Esta Release substitui a publicação automática anterior; o workflow apenas compila, testa e anexa os pacotes ao rascunho do mantenedor
