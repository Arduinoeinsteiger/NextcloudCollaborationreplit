// SwissAirDry Sekundäres Board für Wemos D1 Mini
// Erweiterungsboard für zusätzliche Sensoren und Funktionen
// Kommunikation über I2C mit dem Hauptboard

#include <Wire.h>
#include <ESP8266WiFi.h>
#include <EEPROM.h>

// ----- HARDWARE-KONFIGURATION -----
#define LED_PIN 2         // GPIO2 (D4 auf Wemos D1 Mini) - Blau LED on-board
#define LED_ON LOW        // LED ist aktiv LOW (invertiert)
#define LED_OFF HIGH

// Freie Pins für Sensoren und Aktoren
#define GPIO_D5 D5        // Freier GPIO-Pin
#define GPIO_D6 D6        // Freier GPIO-Pin
#define GPIO_D7 D7        // Freier GPIO-Pin
#define GPIO_D8 D8        // Freier GPIO-Pin
#define ANALOG_PIN A0     // Analoger Eingang

// I2C-Konfiguration
FQBN: esp8266:esp8266:d1_mini_clone
Verwende das Board 'd1_mini_clone' von der Plattform im Ordner: C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2
Verwendung des Kerns 'esp8266' von Platform im Ordner: C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2

"C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\tools\\python3\\3.7.2-post1/python3" -I "C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2/tools/mkbuildoptglobals.py" "C:\\Program Files\\Arduino IDE\\resources\\app\\lib\\backend\\resources" 10607 "C:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF" "C:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF/core/build.opt" "C:\\Users\\gobet\\AppData\\Local\\Temp\\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\\sketch_apr22b/sketch_apr22b.ino.globals.h" "C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2\\cores\\esp8266/CommonHFile.h"
default_encoding:       cp1252
Assume aggressive 'core.a' caching enabled.
Note: optional global include file 'C:\Users\gobet\AppData\Local\Temp\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\sketch_apr22b\sketch_apr22b.ino.globals.h' does not exist.
  Read more at https://arduino-esp8266.readthedocs.io/en/latest/faq/a06-global-build-options.html
Verwendete Bibliotheken erkennen ...
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF\sketch\sketch_apr22b.ino.cpp -o nul
Alternativen für Wire.h: [Wire@1.0]
ResolveLibrary(Wire.h)
  -> Kandidaten: [Wire@1.0]
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF\sketch\sketch_apr22b.ino.cpp -o nul
Alternativen für ESP8266WiFi.h: [ESP8266WiFi@1.0]
ResolveLibrary(ESP8266WiFi.h)
  -> Kandidaten: [ESP8266WiFi@1.0]
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF\sketch\sketch_apr22b.ino.cpp -o nul
Alternativen für EEPROM.h: [EEPROM@1.0]
ResolveLibrary(EEPROM.h)
  -> Kandidaten: [EEPROM@1.0]
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF\sketch\sketch_apr22b.ino.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire\Wire.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\BearSSLHelpers.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\CertStoreBearSSL.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFi.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiAP.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiGeneric.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiGratuitous.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiMulti.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiSTA-WPS.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiSTA.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\ESP8266WiFiScan.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\WiFiClient.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\WiFiClientSecureBearSSL.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\WiFiServer.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\WiFiServerSecureBearSSL.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\WiFiUdp.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src\enable_wifi_at_boot_time.cpp -o nul
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM\EEPROM.cpp -o nul
Funktionsprototypen werden generiert ...
C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\tools\xtensa-lx106-elf-gcc\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++ -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 @C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core/build.opt -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/lwip2/include -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include -IC:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF/core -c @C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2/tools/warnings/none-cppflags -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -w -x c++ -E -CC -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 -DARDUINO_BOARD="ESP8266_WEMOS_D1MINI" -DARDUINO_BOARD_ID="d1_mini_clone" -DFLASHMODE_DOUT -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\cores\esp8266 -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\variants\d1_mini -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi\src -IC:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM C:\Users\gobet\AppData\Local\arduino\sketches\CA913D14A7C7B31699C1833076B221FF\sketch\sketch_apr22b.ino.cpp -o C:\Users\gobet\AppData\Local\Temp\463367217\sketch_merged.cpp
C:\Users\gobet\AppData\Local\Arduino15\packages\builtin\tools\ctags\5.8-arduino11/ctags -u --language-force=c++ -f - --c++-kinds=svpf --fields=KSTtzns --line-directives C:\Users\gobet\AppData\Local\Temp\463367217\sketch_merged.cpp

Sketch wird kompiliert ...
"C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\tools\\python3\\3.7.2-post1/python3" -I "C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2/tools/signing.py" --mode header --publickey "C:\\Users\\gobet\\AppData\\Local\\Temp\\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\\sketch_apr22b/public.key" --out "C:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF/core/Updater_Signing.h"
"C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\tools\\xtensa-lx106-elf-gcc\\3.1.0-gcc10.3-e5f9fec/bin/xtensa-lx106-elf-g++" -D__ets__ -DICACHE_FLASH -U__STRICT_ANSI__ -D_GNU_SOURCE -DESP8266 "@C:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF/core/build.opt" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2/tools/sdk/include" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2/tools/sdk/lwip2/include" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2/tools/sdk/libc/xtensa-lx106-elf/include" "-IC:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF/core" -c "@C:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2/tools/warnings/extra-cppflags" -Os -g -free -fipa-pta -Werror=return-type -mlongcalls -mtext-section-literals -fno-rtti -falign-functions=4 -std=gnu++17 -MMD -ffunction-sections -fdata-sections -fno-exceptions -DMMU_IRAM_SIZE=0x8000 -DMMU_ICACHE_SIZE=0x8000 -DNONOSDK22x_190703=1 -DF_CPU=80000000L -DLWIP_OPEN_SRC -DTCP_MSS=536 -DLWIP_FEATURES=1 -DLWIP_IPV6=0 -DARDUINO=10607 -DARDUINO_ESP8266_WEMOS_D1MINI -DARDUINO_ARCH_ESP8266 "-DARDUINO_BOARD=\"ESP8266_WEMOS_D1MINI\"" "-DARDUINO_BOARD_ID=\"d1_mini_clone\"" -DFLASHMODE_DOUT "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2\\cores\\esp8266" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2\\variants\\d1_mini" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2\\libraries\\Wire" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2\\libraries\\ESP8266WiFi\\src" "-IC:\\Users\\gobet\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.1.2\\libraries\\EEPROM" "C:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF\\sketch\\sketch_apr22b.ino.cpp" -o "C:\\Users\\gobet\\AppData\\Local\\arduino\\sketches\\CA913D14A7C7B31699C1833076B221FF\\sketch\\sketch_apr22b.ino.cpp.o"
C:\Users\gobet\AppData\Local\Temp\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\sketch_apr22b\sketch_apr22b.ino: In function 'void setup()':
C:\Users\gobet\AppData\Local\Temp\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\sketch_apr22b\sketch_apr22b.ino:53:12: warning: unused variable 'chipId' [-Wunused-variable]
   53 |   uint16_t chipId = ESP.getChipId() & 0xFFFF;
      |            ^~~~~~
C:\Users\gobet\AppData\Local\Temp\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\sketch_apr22b\sketch_apr22b.ino:53:45: error: expected '}' at end of input
   53 |   uint16_t chipId = ESP.getChipId() & 0xFFFF;
      |                                             ^
C:\Users\gobet\AppData\Local\Temp\.arduinoIDE-unsaved2025322-38864-1e6jefy.72p2\sketch_apr22b\sketch_apr22b.ino:44:14: note: to match this '{'
   44 | void setup() {
      |              ^
Bibliothek Wire in Version 1.0 im Ordner: C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\Wire  wird verwendet
Bibliothek ESP8266WiFi in Version 1.0 im Ordner: C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\ESP8266WiFi  wird verwendet
Bibliothek EEPROM in Version 1.0 im Ordner: C:\Users\gobet\AppData\Local\Arduino15\packages\esp8266\hardware\esp8266\3.1.2\libraries\EEPROM  wird verwendet
exit status 1

sekundary code
Compilation error: expected '}' at end of input#define I2C_SLAVE_ADDR 0x42  // I2C-Slave-Adresse des Sekundärboards

// Datenstruktur für den Austausch mit dem Hauptboard
struct SensorData {
  float temperature;       // Temperatur in °C
  float humidity;          // Luftfeuchtigkeit in %
  float pressure;          // Luftdruck in hPa
  float voltage;           // Spannung in V
  uint16_t light;          // Lichtsensor-Wert
  uint8_t status;          // Status-Flags
};

SensorData sensorData;     // Aktuelle Sensordaten
bool hasNewData = false;   // Flag für neue Daten

// Puffer für eingehende I2C-Befehle
volatile uint8_t receiveBuffer[32];
volatile uint8_t receiveIndex = 0;

// Hostname mit eindeutiger Chip-ID
String hostname = "SwissAirDry-Secondary-";

void setup() {
  // Serielle Verbindung starten
  Serial.begin(115200);
  Serial.println("\n\nSwissAirDry Secondary Board");

  // EEPROM initialisieren (für Einstellungen)
  EEPROM.begin(512);

  // Eindeutigen Hostnamen erstellen
  uint16_t chipId = ESP.getChipId() & 0xFFFF;
  hostname += String(chipId, HEX);
  Serial.print("Hostname: ");
  Serial.println(hostname);

  // LED konfigurieren
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LED_OFF);

  // GPIOs konfigurieren
  pinMode(GPIO_D5, INPUT_PULLUP);  // Kann nach Bedarf geändert werden
  pinMode(GPIO_D6, INPUT_PULLUP);  // Kann nach Bedarf geändert werden
  pinMode(GPIO_D7, OUTPUT);        // Kann nach Bedarf geändert werden
  pinMode(GPIO_D8, OUTPUT);        // Kann nach Bedarf geändert werden

  // I2C als Slave starten
  Wire.begin(I2C_SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  
  Serial.println("I2C-Slave gestartet, bereit für Kommunikation");
  Serial.print("I2C-Adresse: 0x");
  Serial.println(I2C_SLAVE_ADDR, HEX);

  // Initialisierung der Sensordaten
  resetSensorData();

  // Bereit-Signal mit LED
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LED_ON);
    delay(100);
    digitalWrite(LED_PIN, LED_OFF);
    delay(100);
  }
}

void loop() {
  // Sensoren regelmäßig auslesen
  readSensors();
  
  // Status-LED blinken lassen (Heartbeat)
  static unsigned long lastBlinkTime = 0;
  if (millis() - lastBlinkTime > 5000) { // Alle 5 Sekunden
    lastBlinkTime = millis();
    digitalWrite(LED_PIN, LED_ON);
    delay(50);
    digitalWrite(LED_PIN, LED_OFF);
  }
  
  // Debug-Ausgabe falls neue Daten verfügbar sind
  static unsigned long lastDebugTime = 0;
  if (hasNewData && millis() - lastDebugTime > 10000) { // Alle 10 Sekunden
    lastDebugTime = millis();
    printSensorData();
    hasNewData = false;
  }
  
  // Auf I2C-Kommunikation warten (wird durch Interrupts behandelt)
  delay(100);
}

// Sensordaten zurücksetzen
void resetSensorData() {
  sensorData.temperature = 0.0;
  sensorData.humidity = 0.0;
  sensorData.pressure = 0.0;
  sensorData.voltage = 0.0;
  sensorData.light = 0;
  sensorData.status = 0;
}

// Sensoren auslesen
void readSensors() {
  // Analogwert vom A0-Pin lesen (z.B. für Lichtsensor)
  int analogValue = analogRead(ANALOG_PIN);
  sensorData.light = analogValue;
  
  // Spannung messen (Beispiel)
  float voltage = analogValue * (3.3 / 1023.0);
  sensorData.voltage = voltage;
  
  // Weitere Sensordaten könnten hier gelesen werden
  // z.B. von DHT22, BMP280, etc.
  
  // Status-Flags aktualisieren (Beispiel)
  if (digitalRead(GPIO_D5) == LOW) {
    sensorData.status |= 0x01;  // Bit 0 setzen
  } else {
    sensorData.status &= ~0x01; // Bit 0 zurücksetzen
  }
  
  hasNewData = true;
}

// I2C-Daten an Master senden
void requestEvent() {
  // Sensordaten als Binärdaten senden
  Wire.write((uint8_t*)&sensorData, sizeof(SensorData));
  
  // LED kurz blinken lassen, um Datenübertragung anzuzeigen
  digitalWrite(LED_PIN, LED_ON);
  delayMicroseconds(100);
  digitalWrite(LED_PIN, LED_OFF);
}

// I2C-Daten vom Master empfangen
void receiveEvent(int numBytes) {
  receiveIndex = 0;
  
  while (Wire.available()) {
    if (receiveIndex < sizeof(receiveBuffer)) {
      receiveBuffer[receiveIndex++] = Wire.read();
    } else {
      // Pufferüberlauf vermeiden
      Wire.read();
    }
  }
  
  // Befehle verarbeiten, wenn mindestens 1 Byte empfangen wurde
  if (receiveIndex > 0) {
    processCommand();
  }
}

// Empfangene Befehle verarbeiten
void processCommand() {
  uint8_t command = receiveBuffer[0];
  
  switch (command) {
    case 0x01:  // Reset-Befehl
      resetSensorData();
      break;
      
    case 0x02:  // GPIO-Befehl
      if (receiveIndex >= 3) {
        uint8_t pin = receiveBuffer[1];
        uint8_t value = receiveBuffer[2];
        
        // GPIO-Pin setzen (Beispiel)
        if (pin == 7) {
          digitalWrite(GPIO_D7, value ? HIGH : LOW);
        } else if (pin == 8) {
          digitalWrite(GPIO_D8, value ? HIGH : LOW);
        }
      }
      break;
      
    case 0x03:  // Konfigurationsbefehl
      // Hier könnten Konfigurationseinstellungen gesetzt werden
      break;
      
    default:
      // Unbekannter Befehl
      break;
  }
}

// Sensordaten zur Debug-Ausgabe anzeigen
void printSensorData() {
  Serial.println("--- Sensordaten ---");
  Serial.print("Licht: ");
  Serial.println(sensorData.light);
  Serial.print("Spannung: ");
  Serial.print(sensorData.voltage);
  Serial.println(" V");
  
  if (sensorData.temperature > 0) {
    Serial.print("Temperatur: ");
    Serial.print(sensorData.temperature);
    Serial.println(" °C");
  }
  
  if (sensorData.humidity > 0) {
    Serial.print("Luftfeuchtigkeit: ");
    Serial.print(sensorData.humidity);
    Serial.println(" %");
  }
  
  if (sensorData.pressure > 0) {
    Serial.print("Luftdruck: ");
    Serial.print(sensorData.pressure);
    Serial.println(" hPa");
  }
  
  Serial.print("Status: 0x");
  Serial.println(sensorData.status, HEX);
  Serial.println("------------------");
}