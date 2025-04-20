#pragma once

#ifdef ESP32C6

// Workaround für den Fehler: 'spi_host_device_t' does not name a type
#ifndef SPI_HOST_DEVICE_HSPI
#define SPI_HOST_DEVICE_HSPI 1
#endif

#ifndef SPI_HOST_DEVICE_VSPI
#define SPI_HOST_DEVICE_VSPI 2
#endif

// Fallback-Enum für ESP32-C6, wenn der Typ nicht definiert ist
#ifdef __cplusplus
extern "C" {
#endif

#ifndef spi_host_device_t_defined
#define spi_host_device_t_defined

typedef enum {
    SPI1_HOST = SPI_HOST_DEVICE_HSPI,    // SPI1 (HSPI) ist SPI Host 1
    SPI2_HOST = SPI_HOST_DEVICE_VSPI,    // SPI2 (VSPI) ist SPI Host 2
    SPI3_HOST = 3,                       // SPI3 ist SPI Host 3
} spi_host_device_t;

#endif // spi_host_device_t_defined

#ifdef __cplusplus
}
#endif

#endif // ESP32C6