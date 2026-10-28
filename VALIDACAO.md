# Validação — ChimpiBridge 0.1.1

Data: 28/10/2026

## Preparação automática do ADB

- 46 testes automatizados aprovados em Linux com Python 3.12.14 e PySide6 6.12.0
- Download ausente, reutilização do cache, hash inválido, tamanho inválido, extração fora da pasta, DLL ausente, falha de rede e preservação do cache anterior cobertos por testes
- Integração da interface cobre preparação em segundo plano, bloqueio de downloads repetidos após falha, repetição manual e ausência de reinício automático do aparelho
- A execução Windows é configurada com `CREATE_NO_WINDOW` e `shell=False`, sem abrir PowerShell
- O arquivo oficial Platform-Tools 37.0.1 para Windows foi baixado do Google e conferido contra tamanho e SHA-1 publicados em `repository2-3.xml` antes de registrar o SHA-256 fixo no aplicativo
- A versão 0.1.1 ainda aguarda a execução Windows do workflow para confirmar o download real, compilação e inicialização do novo EXE

## Versão Windows anterior

A versão 0.1.0 foi compilada, passou em 33 testes no Windows e teve seu EXE aberto/renderizado em modo offscreen

[Execução Windows anterior](https://github.com/Chimpi-hackintosh/ChimpiBridge/actions/runs/40747432139)

## Verificação em hardware ainda pendente

- Comunicação USB e troca de modos em celulares reais
- Recovery de fábrica e/ou TWRP nos modelos utilizados
- Execução em Windows de teste sem Python previamente instalado
- Instalação, atualização e desinstalação do setup preparado pelo mantenedor

Os testes de aparelho usam adaptadores simulados
O setup instalável permanece a cargo de Chimpi-hackintosh, a partir da distribuição pronta
Download Mode, Fastboot e iPhone continuam planejados
