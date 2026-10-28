# Validação — ChimpiBridge 0.1.0

Data: 28/10/2026

## Build Windows publicado

O pacote portátil com **ChimpiBridge.exe** foi gerado em um runner **Windows 2025 x64**, usando Python 3.12.10

[Execução verificada no GitHub Actions](https://github.com/Chimpi-hackintosh/ChimpiBridge/actions/runs/40747432139)

[Release v0.1.0 com o pacote Windows pronto](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases/tag/v0.1.0)

| Verificação | Resultado |
|---|---|
| Testes de núcleo e recursos no Windows | 26 aprovados |
| Testes de integração da interface Qt no Windows | 7 aprovados |
| Total de testes automatizados no Windows | **33 aprovados** |
| Geração do EXE Windows x64 por PyInstaller | Aprovada |
| Verificação do formato de executável Windows PE | Aprovada |
| Abertura do EXE compilado a partir de outro diretório de trabalho | Aprovada |
| Renderização da janela e do ícone SVG em modo offscreen | Aprovada |
| Localização do ADB incluído no pacote | Aprovada |
| Publicação do ZIP portátil e do arquivo SHA-256 na Release | Concluída |

O pacote publicado é **ChimpiBridge-0.1.0-windows-x64-portable.zip**
Ele contém o EXE, o runtime Python, as bibliotecas, os recursos, as traduções e as ferramentas ADB
A pasta inteira deve ser mantida junto do executável

O setup instalável será preparado separadamente por **Chimpi-hackintosh**, a partir dessa distribuição pronta

## Verificações anteriores

Os mesmos 33 testes também passaram no ambiente Linux com Python 3.12.14 e Qt/PySide6 6.12.0
A interface foi inspecionada em português e inglês, incluindo a janela mínima de 950 × 650 com rolagem

Os testes cobrem vários aparelhos, autorização revogada, desconexão, sideload, falhas e timeout do ADB, falta de evidência de boot, seleção por serial, confirmação de modo, persistência, traduções e manifesto de desinstalação

## Ainda depende de verificação em hardware

- Comunicação USB e troca de modos em celulares reais
- Recovery de fábrica e/ou TWRP em cada modelo suportado
- Execução em um Windows de teste sem Python previamente instalado
- Instalação, atualização, atalhos e desinstalação do setup que o mantenedor preparar

Os testes de aparelho usam adaptadores simulados
O teste do EXE verifica inicialização, recursos, renderização e presença do ADB; ele não usa um celular físico
O instalador NSIS não foi compilado nesta publicação

Download Mode, Fastboot e iPhone permanecem no planejamento das próximas versões
