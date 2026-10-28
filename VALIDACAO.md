# Validação — ChimpiBridge 0.1.0

Data: 27/10/2026

## Executado nesta entrega

Ambiente: Linux, Python 3.12.14 e Qt/PySide6 6.12.0

| Verificação | Resultado |
|---|---|
| Testes de núcleo e recursos | 26 aprovados |
| Testes de integração da interface Qt | 7 aprovados |
| Total automatizado | **33 aprovados** |
| Compilação sintática dos arquivos Python | Aprovada |
| Renderização da interface em português e inglês | Inspecionada em modo offscreen |
| Janela mínima de 950 × 650 e guia de conexão | Inspecionados, com rolagem para preservar o conteúdo |

Os cenários testados incluem vários aparelhos conectados, autorização revogada, desconexão antes do comando, estado sideload, falha e timeout do ADB, ausência de evidência de boot, seleção explícita por serial e confirmação de Recovery somente no aparelho escolhido

Também foram verificados persistência de preferências e histórico, equivalência das traduções, troca de idioma durante acompanhamento, formatação textual do histórico e geração do manifesto de desinstalação sem remoção recursiva de dados do usuário

Os testes de dispositivo e de interface usam adaptadores simulados — não substituem testes em hardware
A execução literal de argumentos do subprocesso foi verificada com um processo Python real

## Ainda depende de Windows e hardware reais

- Geração do EXE por PyInstaller no Windows x64
- Compilação e execução do instalador NSIS
- Abertura do EXE em Windows sem Python instalado
- Detecção dos idiomas de exibição pelas APIs do Windows
- Teste USB em aparelhos reais, com recovery de fábrica e/ou TWRP
- Instalação, atualização, atalhos e desinstalação com preservação de dados

Nenhum EXE Windows foi compilado nesta entrega
O instalador foi escrito e revisado, mas não foi compilado nem executado neste ambiente

## Roteiro prático de verificação no Windows

1. Gere o pacote com `build_windows.cmd`, usando a pasta oficial completa do Platform-Tools
2. Instale em uma máquina de teste e abra o atalho com uma conta comum
3. Confira português, inglês e o fallback de um idioma não disponível
4. Conecte dois aparelhos e confirme que é necessário selecionar o alvo
5. Confira os estados não autorizado e offline antes de autorizar a conexão
6. Solicite Recovery em um aparelho de teste e observe a tela do celular e o resultado no app
7. Reinicie para o Android e confira a confirmação de inicialização
8. Feche e reabra, depois atualize e desinstale, conferindo a preservação das preferências e do histórico

Download Mode, Fastboot e iPhone permanecem no planejamento das próximas versões
