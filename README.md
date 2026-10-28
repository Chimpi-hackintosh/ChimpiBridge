# ChimpiBridge 0.1.0

Gerenciador desktop de conexão e modos Android, escrito em **Python + PySide6**

**O setup oficial para Windows é preparado e publicado por Chimpi-hackintosh, mantenedor do projeto**

Os usuários baixam e instalam o setup pronto disponibilizado pelo mantenedor nas [Releases](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases)
A preparação do executável e do instalador fica a cargo de Chimpi-hackintosh

Este repositório também reúne o código-fonte e as ferramentas usadas no desenvolvimento

## O que está implementado

- Detecção de aparelhos visíveis pelo ADB e seleção explícita do aparelho
- Estados Android/ADB, Recovery, offline, não autorizado e sideload
- Reinício normal e entrada no recovery já instalado no celular
- Conferência da presença e autorização imediatamente antes de enviar o comando
- Acompanhamento da reconexão por até 90 segundos, com confirmação baseada no aparelho selecionado
- Histórico local, exportação para texto e preferências persistentes
- Interface em português e inglês, com idioma de exibição do Windows e opção de troca manual
- Guia de conexão, seleção do ADB e links oficiais de download e drivers
- Operações em segundo plano, sem executar comandos pelo shell do computador

## Instalação e uso no Windows

**Quem prepara o setup: Chimpi-hackintosh**

1. Acesse as [Releases do ChimpiBridge](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases)
2. Quando o setup oficial estiver disponível, baixe a versão publicada por Chimpi-hackintosh
3. Execute o instalador e abra o ChimpiBridge pelo atalho criado
4. Conecte o Android com um cabo USB de dados
5. Ative a depuração USB no celular e autorize a conexão com o computador
6. Selecione o aparelho no aplicativo e escolha **Entrar no Recovery** ou **Reiniciar Android**

O setup oficial deve entregar o aplicativo com o runtime Python, as bibliotecas e as ferramentas ADB incluídos
Para usar essa distribuição pronta, o usuário instala o setup e segue o guia de conexão do aplicativo
Os drivers USB do fabricante podem ser necessários para o computador reconhecer o aparelho

## Área do mantenedor

A compilação, o empacotamento, os testes da distribuição e a publicação do setup oficial são realizados por **Chimpi-hackintosh**
Os scripts de desenvolvimento e build abaixo servem à preparação dessas versões pelo mantenedor

<details>
<summary>Instruções de desenvolvimento e empacotamento para o mantenedor</summary>

### Executar o código-fonte para desenvolvimento

As instruções desta área são para o mantenedor preparar e testar as versões

1. Instale **Python 3.12 x64**, incluindo o Python Launcher (`py`)
2. Extraia este projeto para uma pasta comum do seu usuário
3. Abra **run_windows.cmd** — ele cria um ambiente virtual, instala a dependência e abre a interface
4. Use **Baixar Platform-Tools** para abrir a página oficial do Android e baixe o ZIP para Windows
5. Extraia o ZIP inteiro e use **Escolher ADB** para selecionar `adb.exe` dentro da pasta extraída
6. Ative a depuração USB no Android, conecte um cabo de dados e aceite a autorização na tela do aparelho
7. Selecione o celular e use **Entrar no Recovery** ou **Reiniciar Android**

Os arquivos DLL que acompanham `adb.exe` precisam permanecer junto dele
Se a conexão não aparecer, siga a aba **Como conectar** e o link dos drivers do fabricante
O aplicativo reconhece os estados informados pelo ADB e oferece orientações para conferir os drivers USB do fabricante

O comando do Python deve estar disponível como `py -3.12` para usar os arquivos CMD
Se você já tem outra versão compatível do Python, pode usar os comandos manuais abaixo em um ambiente virtual próprio

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

### Preparar o executável e o setup oficial

O build precisa rodar em **Windows x64**, usando Python x64
O destino previsto é Windows 10 versão 1809 ou posterior / Windows 11

1. Instale o [NSIS 3](https://nsis.sourceforge.io/Download)
2. Extraia a pasta oficial completa `platform-tools` dentro de `tools/`
3. Confira `tools/platform-tools/adb.exe`, as DLLs, `NOTICE.txt` e `source.properties`
4. Abra **build_windows.cmd**

O script executa os testes do núcleo, gera o aplicativo, prepara o diretório real de distribuição, verifica a ausência de fontes `.py`/`.pyw` e só então cria o instalador

Arquivos gerados após um build bem-sucedido no Windows:

| Caminho | Conteúdo |
|---|---|
| `dist/ChimpiBridge/` | EXE, runtime Python, bibliotecas, ferramentas ADB e recursos separados |
| `release/ChimpiBridge-0.1.0-windows-x64-portable.zip` | Pacote portátil completo — distribua a pasta inteira |
| `release/ChimpiBridge-0.1.0-windows-x64-setup.exe` | Instalador NSIS com desinstalação e atalhos |

Para usar uma pasta Platform-Tools já existente:

```bat
build_windows.cmd --platform-tools "C:\Android\platform-tools"
```

Para gerar somente o pacote portátil, sem precisar de NSIS:

```bat
build_windows.cmd --portable-only
```

O instalador usa `Program Files\SnoopyOS Company\ChimpiBridge`, registra a desinstalação e cria um atalho no menu Iniciar
O atalho da área de trabalho é opcional
O app instalado inclui o Python e suas dependências, funcionando como usuário comum
O instalador por máquina pede elevação; o aplicativo não a solicita

Configurações e histórico ficam em `%LOCALAPPDATA%\SnoopyOS Company\ChimpiBridge`
Atualizações e desinstalação preservam essa pasta
O desinstalador remove somente os arquivos listados no staging e diretórios que estiverem vazios

</details>

## O que a confirmação significa

Enviar um comando com sucesso produz **Solicitação enviada**, seguido de acompanhamento
Para Recovery, o aplicativo espera evidência de modo recovery no mesmo identificador ADB
Para reinício normal, ele espera Android com `sys.boot_completed=1` e evidência de uma nova inicialização — desconexão observada, mudança do identificador do boot ou transição a partir do Recovery

Se o aparelho mudar de identificador ao reiniciar, bloquear o ADB no Recovery, omitir propriedades ou ficar em outro modo, o resultado será **não confirmado**
Isso não prova que o reinício falhou — confira a tela do aparelho
Encerrar o acompanhamento interrompe apenas a verificação do aplicativo

Recovery de fábrica, TWRP e outras recuperações oferecem recursos ADB diferentes
O aplicativo abre o recovery instalado, sem instalar uma recuperação nova
Depuração USB e autorização são necessárias para enviar comandos a um Android iniciado normalmente

## Próximas versões

| Etapa | Escopo | Estado |
|---|---|---|
| 0.1 | Android por ADB, reinício, Recovery e histórico | Implementado neste projeto |
| 0.2 | Fastboot, Fastbootd, Download Mode Samsung e detecção própria desses protocolos | Planejado — compatibilidade por modelo ainda precisa de validação |
| 0.3 | iPhone por libimobiledevice/libirecovery e assistente DFU por modelo | Planejado — ainda sem backend iOS neste projeto |

Download Mode Samsung e Fastboot não são confirmados por uma listagem ADB
Eles exigem adaptadores específicos; não há controles desses modos nesta versão
O iPhone também precisa de integração própria, com protocolos diferentes do ADB

## Testes de desenvolvimento

Para o mantenedor, com as dependências instaladas:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes de interface usam Qt em modo offscreen e um adaptador ADB injetado
Eles não acessam um celular real
Veja **VALIDACAO.md** para os resultados e as verificações Windows que ainda dependem de execução real

## Organização

| Pasta/arquivo | Responsabilidade |
|---|---|
| `main.py` | Inicialização do aplicativo |
| `chimpibridge/adb.py` | Execução do ADB, leitura de estados e confirmação de transições |
| `chimpibridge/ui.py` | Interface e coordenação de trabalhos em segundo plano |
| `chimpibridge/storage.py` | Recursos externos, preferências e histórico |
| `chimpibridge/i18n.py` | Idioma automático, override e fallback |
| `locales/` | Traduções completas pt-BR e inglês |
| `assets/` | Estilo, ícone vetorial e ícone Windows |
| `scripts/build_windows.py` | Build e empacotamento Windows |
| `installer/ChimpiBridge.nsi` | Instalador NSIS |
| `tests/` | Testes de núcleo e interface |

## Fontes oficiais consultadas

- [Android Debug Bridge](https://developer.android.com/tools/adb)
- [Manual do ADB](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md)
- [Qt for Python](https://doc.qt.io/qtforpython-6/)
- [Plataformas do Qt](https://doc.qt.io/qt-6/supported-platforms.html)
- [PyInstaller](https://pyinstaller.org/en/stable/)
- [Referência do NSIS](https://nsis.sourceforge.io/Docs/Chapter4.html)
- [libimobiledevice — planejamento iPhone](https://github.com/libimobiledevice/libimobiledevice)
- [libirecovery — planejamento iPhone](https://github.com/libimobiledevice/libirecovery)

O código do projeto usa a licença MIT presente em **LICENSE**
Os avisos dos componentes externos estão em **THIRD_PARTY_NOTICES.md**
