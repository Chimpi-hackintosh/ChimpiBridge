# ChimpiBridge 0.1.1 — Windows x64

Primeira versão do gerenciador Android em Python + PySide6

## Download pronto para usar

Baixe **ChimpiBridge-0.1.1-windows-x64-portable.zip**, extraia a pasta inteira e abra **ChimpiBridge.exe**

O pacote inclui o executável, o runtime Python, as bibliotecas e as ferramentas ADB
Mantenha as pastas que acompanham o EXE junto dele
Não é necessário compilar o projeto nem instalar Python para usar este pacote

O setup instalável é preparado separadamente por **Chimpi-hackintosh**, usando a distribuição pronta

## Novo nesta versão

- Preparação automática do ADB no Windows quando ausente, sem abrir console ou PowerShell
- Download direto do Google, conferência de SHA-256 antes da execução e reutilização no perfil do usuário
- Botão para repetir a preparação após falha de rede, sem downloads em loop

## Funcionalidades

- Detecção e seleção de aparelhos Android visíveis pelo ADB
- Reinício normal e entrada no Recovery já instalado no aparelho
- Acompanhamento de reconexão e confirmação de modo quando o aparelho fornece as informações necessárias
- Histórico local, exportação de relatório e interface em português e inglês

## Compatibilidade e verificação

- Windows 10 versão 1809 ou posterior / Windows 11, x64
- Testes de lógica e interface executados no Windows
- Executável aberto e renderizado em teste de inicialização no runner Windows
- Comunicação com celulares físicos ainda depende de teste por USB
- Depuração USB, autorização no celular e o driver do fabricante podem ser necessários

Download Mode Samsung, Fastboot/Fastbootd e iPhone permanecem planejados para versões futuras

O arquivo `.sha256` permite conferir a integridade do ZIP
