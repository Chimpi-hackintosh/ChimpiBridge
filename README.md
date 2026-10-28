# ChimpiBridge 0.1.1

**Autor e mantenedor: [Chimpi-hackintosh](https://github.com/Chimpi-hackintosh)**

**Versão atual: [0.1.1](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases/tag/v0.1.1)**

Gerenciador desktop de conexão e modos Android para **Windows e macOS**, escrito em **Python + PySide6**

**O setup oficial para Windows é preparado e publicado por Chimpi-hackintosh, mantenedor do projeto**

O pacote portátil com o EXE pronto está nas [Releases](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases/tag/v0.1.1)
A criação e a publicação do setup instalável ficam com **Chimpi-hackintosh**, a partir desse pacote pronto

Este repositório também reúne o código-fonte e as ferramentas usadas no desenvolvimento

## O que está implementado

- Detecção de aparelhos visíveis pelo ADB e seleção explícita do aparelho
- Estados Android/ADB, Recovery, offline, não autorizado e sideload
- Reinício normal e entrada no recovery já instalado no celular
- Conferência da presença e autorização imediatamente antes de enviar o comando
- Acompanhamento da reconexão por até 90 segundos, com confirmação baseada no aparelho selecionado
- Histórico local, exportação para texto e preferências persistentes
- Interface em português e inglês, com idioma de exibição do Windows e opção de troca manual
- Preparação automática do ADB oficial no Windows quando a ferramenta está ausente, com SHA-256 e cache local
- Guia de conexão, seleção avançada do ADB e links oficiais para drivers
- Operações em segundo plano, sem executar comandos pelo shell do computador

## Usar o EXE pronto no Windows

1. Acesse as [Releases do ChimpiBridge](https://github.com/Chimpi-hackintosh/ChimpiBridge/releases/tag/v0.1.1)
2. Baixe **ChimpiBridge-0.1.1-windows-x64-portable.zip**
3. Extraia a pasta inteira do ZIP
4. Abra **ChimpiBridge.exe** dentro da pasta extraída
5. Conecte o Android com um cabo USB de dados e autorize a depuração USB no celular
6. Selecione o aparelho e escolha **Entrar no Recovery** ou **Reiniciar Android**

O pacote inclui o EXE, o runtime Python, as bibliotecas e as ferramentas ADB
Mantenha o EXE e todas as pastas que o acompanham juntos
Para usar essa versão pronta, basta extrair o pacote e abrir o aplicativo
Os drivers USB do fabricante podem ser necessários para reconhecer o celular

**O setup instalável é preparado separadamente por Chimpi-hackintosh**
O mantenedor pode usar a pasta completa da distribuição portátil como origem do seu instalador

## ADB em segundo plano

O pacote portátil já inclui o ADB completo
Se a ferramenta estiver ausente no Windows, o aplicativo baixa o **SDK Platform-Tools 37.0.1** diretamente do Google, verifica o SHA-256 antes de executar qualquer arquivo e extrai o pacote para a pasta de dados do usuário
Não é preciso abrir PowerShell, digitar comandos, alterar o PATH ou executar o aplicativo como administrador

A detecção usa `adb devices -l`
Um único aparelho é selecionado automaticamente; com vários aparelhos, escolha o destino na lista
Ao clicar em **Entrar no Recovery**, o aplicativo executa internamente:

```text
adb -s SERIAL reboot recovery
```

O processo é iniciado sem janela de console, usando o serial selecionado
A autorização da depuração USB continua sendo aceita na tela do Android
O aplicativo acompanha a reconexão e só confirma o Recovery quando observa esse modo no mesmo aparelho

A ferramenta baixada fica em `%LOCALAPPDATA%\SnoopyOS Company\ChimpiBridge\tools\platform-tools-37.0.1\platform-tools`
Ela é reutilizada nas próximas aberturas
Se a internet falhar, o aplicativo mostra o erro e oferece **Preparar ADB** para tentar novamente, sem repetir downloads em loop
Uma ferramenta escolhida manualmente mantém precedência sobre a preparação automática

## EXE independente para Windows

Como alternativa ao ZIP portátil, baixe **ChimpiBridge-0.1.1-windows-x64.exe** na mesma Release
Esse arquivo inclui o runtime e a interface e pode ser aberto sozinho, sem instalar Python
Quando necessário, o ADB é baixado do Google e preparado na pasta de dados do usuário — a primeira preparação exige internet
O pacote ZIP continua incluindo o ADB para uso sem esse download inicial

## App para macOS

- **ChimpiBridge-0.1.1-macos-arm64.zip** para Apple Silicon
- **ChimpiBridge-0.1.1-macos-x64.zip** para Intel

Extraia o ZIP e mova **ChimpiBridge.app** para **Aplicativos**
O app inclui Python, Qt e o ADB; o requisito mínimo é macOS 14.4
As versões macOS têm assinatura ad hoc local, sem notarização Apple
Preferências e histórico ficam em `~/Library/Application Support/SnoopyOS Company/ChimpiBridge`
O suporte atual continua sendo Android por ADB; o backend iPhone permanece planejado

## Publicação em nome do mantenedor

O rascunho da Release é criado pela conta **Chimpi-hackintosh**
O workflow compila, testa e anexa os arquivos a esse rascunho, sem criar Releases em nome do bot
A publicação final é feita pela conta do mantenedor
A publicação automática anterior é preservada como rascunho de backup, com sua revisão e arquivos originais

## Área do mantenedor

O workflow gera e verifica ZIP e EXE independente Windows e apps macOS Intel e Apple Silicon nos respectivos sistemas
**Chimpi-hackintosh cuida da criação e publicação do setup instalável** a partir da pasta pronta
As instruções abaixo documentam o desenvolvimento e o empacotamento manual, quando necessários

<details>
<summary>Instruções de desenvolvimento e empacotamento para o mantenedor</summary>

### Executar o código-fonte para desenvolvimento

As instruções desta área são para o mantenedor preparar e testar as versões

1. Instale **Python 3.12 x64**, incluindo o Python Launcher (`py`)
2. Extraia este projeto para uma pasta comum do seu usuário
3. Abra **run_windows.cmd** — ele cria um ambiente virtual, instala a dependência e abre a interface
4. No Windows, aguarde a preparação automática do ADB se nenhuma ferramenta estiver disponível
5. Ative a depuração USB no Android, conecte um cabo de dados e aceite a autorização na tela do aparelho
6. Selecione o celular e use **Entrar no Recovery** ou **Reiniciar Android**

**Escolher ADB** permite usar uma instalação própria da ferramenta, quando necessário

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
| `release/ChimpiBridge-0.1.1-windows-x64-portable.zip` | Pacote portátil completo — distribua a pasta inteira |
| `release/ChimpiBridge-0.1.1-windows-x64-setup.exe` | Instalador NSIS com desinstalação e atalhos |

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

## Sintaxe proposta das ações

Os exemplos `from adb action reboot to recovery` e `from cfgutil action=reboot to=recovery ./apple ./action-time=now` descrevem o fluxo desejado do projeto
A versão atual usa os botões da interface; o interpretador dessa sintaxe e o backend Apple ainda não estão implementados
Veja [Fluxos de ações Android e Apple](docs/acoes.md) para o mapeamento atual do ADB e os requisitos do cfgutil no macOS

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
| `chimpibridge/provision.py` | Download oficial verificado e cache do ADB no perfil do usuário |
| `chimpibridge/ui.py` | Interface e coordenação de trabalhos em segundo plano |
| `chimpibridge/storage.py` | Recursos externos, preferências e histórico |
| `chimpibridge/i18n.py` | Idioma automático, override e fallback |
| `locales/` | Traduções completas pt-BR e inglês |
| `assets/` | Estilo, ícone vetorial e ícone Windows |
| `scripts/build_windows.py` | Build e empacotamento Windows |
| `scripts/build_macos.py` | Build e verificação dos apps macOS |
| `scripts/release_packages.py` | Anexos no rascunho do mantenedor e preservação da publicação anterior |
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
