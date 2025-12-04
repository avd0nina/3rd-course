/*
 * Copyright (c) 2009-2014 Kazuho Oku, Tokuhiro Matsuno, Daisuke Murase,
 *                         Shigeo Mitsunari
 *
 * The software is licensed under either the MIT License (below) or the Perl
 * license.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#ifndef picohttpparser_h
#define picohttpparser_h

#include <sys/types.h>

#ifdef _MSC_VER
#define ssize_t intptr_t
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Структура, представляющая HTTP-заголовок
 * @details Содержит имя и значение заголовка.
 * @var name       Указатель на начало имени заголовка
 * @var name_len   Длина имени заголовка в байтах
 * @var value      Указатель на начало значения заголовка
 * @var value_len  Длина значения заголовка в байтах
 */
struct phr_header {
    const char *name;
    size_t name_len;
    const char *value;
    size_t value_len;
};

/**
 * @brief Разбирает HTTP-запрос из буфера
 * @param buf           Буфер с HTTP-запросом
 * @param len           Длина данных в буфере
 * @param method        Возвращаемый указатель на метод запроса (GET, POST и т.д.)
 * @param method_len    Возвращаемая длина метода
 * @param path          Возвращаемый указатель на путь запроса
 * @param path_len      Возвращаемая длина пути
 * @param minor_version Возвращаемая минорная версия HTTP (0 для HTTP/1.0, 1 для HTTP/1.1)
 * @param headers       Массив для заполнения заголовков
 * @param num_headers   Вход: емкость массива headers; Выход: количество найденных заголовков
 * @param last_len      Длина предыдущего частичного запроса (0 при первом вызове)
 * @return >0  - количество обработанных байт
 *         -1  - ошибка разбора
 *         -2  - неполный запрос (нужно больше данных)
 */
int phr_parse_request(const char *buf, size_t len, const char **method, size_t *method_len, const char **path, size_t *path_len,
                      int *minor_version, struct phr_header *headers, size_t *num_headers, size_t last_len);

/**
 * @brief Разбирает HTTP-ответ из буфера
 * @param _buf          Буфер с HTTP-ответом (не нуль-терминированный)
 * @param len           Длина данных в буфере
 * @param minor_version Возвращаемая минорная версия HTTP
 * @param status        Возвращаемый статус ответа (200, 404, 500 и т.д.)
 * @param msg           Возвращаемый указатель на сообщение статуса ("OK", "Not Found")
 * @param msg_len       Возвращаемая длина сообщения статуса
 * @param headers       Массив для заполнения заголовков
 * @param num_headers   Вход: емкость массива headers; Выход: количество найденных заголовков
 * @param last_len      Длина предыдущего частичного ответа (0 при первом вызове)
 * @return >0  - количество обработанных байт
 *         -1  - ошибка разбора
 *         -2  - неполный ответ (нужно больше данных)
 */
int phr_parse_response(const char *_buf, size_t len, int *minor_version, int *status, const char **msg, size_t *msg_len,
                       struct phr_header *headers, size_t *num_headers, size_t last_len);

/**
 * @brief Разбирает только заголовки HTTP из буфера
 * @param buf           Буфер с HTTP-заголовками (после первой строки)
 * @param len           Длина данных в буфере
 * @param headers       Массив для заполнения заголовков
 * @param num_headers   Вход: емкость массива headers; Выход: количество найденных заголовков
 * @param last_len      Длина предыдущих частичных заголовков (0 при первом вызове)
 * @return >0  - количество обработанных байт
 *         -1  - ошибка разбора
 *         -2  - неполные заголовки (нужно больше данных)
 */
int phr_parse_headers(const char *buf, size_t len, struct phr_header *headers, size_t *num_headers, size_t last_len);

/**
 * @brief Декодер для chunked transfer encoding
 * @details Структура должна быть обнулена перед использованием.
 *          Используется для декодирования данных в формате Transfer-Encoding: chunked.
 * @var bytes_left_in_chunk  Количество байт, оставшихся в текущем чанке
 * @var consume_trailer      Флаг: следует ли потреблять трейлеры (заголовки после чанков)
 * @var _hex_count           Внутренний счетчик для парсинга шестнадцатеричных чисел
 * @var _state               Внутреннее состояние декодера
 */
struct phr_chunked_decoder {
    size_t bytes_left_in_chunk; /* number of bytes left in current chunk */
    char consume_trailer;       /* if trailing headers should be consumed */
    char _hex_count;
    char _state;
};

/**
 * @brief Декодирует данные в формате chunked transfer encoding
 * @details Перезаписывает буфер, удаляя chunked-заголовки. При успешном выполнении
 *          *bufsz обновляется до длины декодированных данных.
 * @param decoder  Указатель на инициализированный декодер (должен быть обнулен)
 * @param buf      Буфер с chunked-данными (будет модифицирован)
 * @param bufsz    Вход: размер буфера; Выход: размер декодированных данных
 * @return >=0 - количество необработанных байт после декодирования
 *         -1  - ошибка декодирования
 *         -2  - неполные данные (нужно больше данных для продолжения)
 * @note Приложения должны повторно вызывать функцию, пока она возвращает -2,
 *       каждый раз предоставляя новые данные.
 */
ssize_t phr_decode_chunked(struct phr_chunked_decoder *decoder, char *buf, size_t *bufsz);

/**
 * @brief Проверяет, находится ли декодер в середине обработки данных чанка
 * @param decoder Указатель на декодер
 * @return 1 если декодер в середине данных чанка, 0 в противном случае
 */
int phr_decode_chunked_is_in_data(struct phr_chunked_decoder *decoder);

#ifdef __cplusplus
}
#endif

#endif
