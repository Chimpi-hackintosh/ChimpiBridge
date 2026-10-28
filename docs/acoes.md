# Fluxos de ações — Android e Apple

Os exemplos a seguir descrevem a intenção de cada ação no ChimpiBridge
Eles são uma proposta de sintaxe interna do projeto; não são comandos nativos do Python, do ADB ou do cfgutil, e a interface 0.1.1 ainda utiliza botões

## Android por ADB — implementado

Intenção proposta:

```text
from adb action reboot to recovery
```

Fluxo usado pelo aplicativo:

1. Localizar a ferramenta escolhida, a cópia incluída na distribuição, o cache local ou uma instalação no PATH
2. Se estiver ausente no Windows e não houver um caminho escolhido manualmente, baixar em segundo plano o pacote oficial fixado do Google
3. Conferir tamanho e SHA-256 do ZIP antes de extrair e executar a ferramenta
4. Listar os aparelhos com `adb devices -l`; selecionar o único aparelho ou aguardar a escolha quando houver vários
5. Aguardar a autorização da depuração USB na tela do Android
6. Ao clicar em Entrar no Recovery, conferir novamente o aparelho selecionado e executar `adb -s SERIAL reboot recovery`
7. Acompanhar a reconexão e a evidência do modo no mesmo identificador

O processo é iniciado diretamente, sem janela de console
A execução usa uma lista de argumentos, `shell=False` e `CREATE_NO_WINDOW` no Windows
O mesmo mecanismo evita a necessidade de abrir PowerShell ou simular digitação

## Apple por cfgutil — intenção registrada, integração pendente

Intenção proposta pelo mantenedor:

```text
from cfgutil action=reboot to=recovery ./apple ./action-time=now
```

O nome da ferramenta de linha de comando do Apple Configurator é `cfgutil`
Ela pertence ao Apple Configurator para **macOS** e deve ser instalada pelo próprio Configurator
O executável não deve ser baixado ou apresentado como uma versão Windows do cfgutil

`./apple` identifica a família de aparelhos nesta proposta de sintaxe
`./action-time=now` indica envio imediato após verificar ferramenta, aparelho selecionado e autorizações
Esses marcadores são dados do planejador proposto, não caminhos ou comandos a serem enviados ao shell

O mapeamento de `action=reboot to=recovery` para cfgutil ainda exige validação na ajuda da versão instalada e em um Mac com aparelho de teste
Nenhum comando cfgutil foi implementado ou executado nesta versão

Para entrada em Recovery por uma integração própria com libimobiledevice, existe a ferramenta `ideviceenterrecovery`, que recebe o UDID do aparelho
Esse backend continua no planejamento do suporte a iPhone, incluindo a detecção posterior do modo pelo mesmo aparelho

A entrada em Recovery e a restauração de firmware são ações distintas
A intenção acima deve somente solicitar o modo, preservando o escopo de reinício

## Fontes

- [SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)
- [Manual do ADB](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md)
- [Automação com o Apple Configurator e cfgutil](https://support.apple.com/guide/deployment/configure-devices-dep6f70f6647/web)
- [Código oficial de ideviceenterrecovery](https://github.com/libimobiledevice/libimobiledevice/blob/master/tools/ideviceenterrecovery.c)
