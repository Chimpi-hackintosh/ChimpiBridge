# Android SDK Platform-Tools

Baixe o ZIP oficial para Windows em https://developer.android.com/tools/releases/platform-tools

Para gerar o pacote Windows com ADB incluído, extraia a pasta inteira aqui:

`tools/platform-tools/adb.exe`

Mantenha `AdbWinApi.dll`, `AdbWinUsbApi.dll`, `NOTICE.txt`, `source.properties` e os demais arquivos originais juntos

No desenvolvimento, você também pode selecionar um ADB já extraído em qualquer pasta usando o botão **Escolher ADB**

O projeto-fonte entregue não inclui binários do Android SDK — o script de build copia a pasta que você fornecer para o pacote final
