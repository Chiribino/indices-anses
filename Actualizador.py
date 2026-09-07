import json
from datetime import datetime
from dateutil.relativedelta import relativedelta


def obtener_ultimo_mes(diccionario):
    fechas = list(diccionario.keys())
    fechas_dt = []
    for fecha in fechas:
        mes, año = fecha.split('/')
        fechas_dt.append((datetime(int(año), int(mes), 1), fecha))
    fechas_dt.sort(key=lambda x: x[0])
    return fechas_dt[-1][1]


def obtener_siguiente_mes(fecha_str):
    mes, año = fecha_str.split('/')
    fecha = datetime(int(año), int(mes), 1)
    siguiente_fecha = fecha + relativedelta(months=1)
    return f"{siguiente_fecha.month:02d}/{siguiente_fecha.year}"


def obtener_proximos_3_meses(fecha_str):
    meses = []
    fecha_actual = fecha_str
    for i in range(3):
        fecha_actual = obtener_siguiente_mes(
            fecha_actual) if i > 0 else obtener_siguiente_mes(fecha_str)
        meses.append(fecha_actual)
        if i == 0:
            fecha_str = fecha_actual
    return meses


def leer_archivo_indices(archivo='indices.json'):
    with open(archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    return {
        'pbus': datos['pbus'],
        'haberes_minimos': datos['haberes_minimos'],
        'haberes_maximos': datos['haberes_maximos'],
        'bases_maximas': datos['bases_maximas'],
        'coeficientes_de_actualizacion': datos['coeficientes_de_actualizacion'],
        'movilidad': datos['movilidad'],
        'monotributo_promovido': datos.get('monotributo_promovido', None),
        'ucap': datos.get('ucap', None),
        'rentas_de_referencia': datos.get('rentas_de_referencia', {}),
        'bonos': datos.get('bonos', {}),
    }


def escribir_archivo_indices(diccionarios, archivo='indices.json'):
    orden_claves = [
        'pbus', 'haberes_minimos', 'haberes_maximos', 'bases_maximas',
        'coeficientes_de_actualizacion', 'movilidad',
        'rentas_de_referencia', 'bonos',
        'monotributo_promovido', 'ucap'
    ]
    datos_ordenados = {}
    for clave in orden_claves:
        if clave in diccionarios:
            datos_ordenados[clave] = diccionarios[clave]
    for clave in diccionarios:
        if clave not in datos_ordenados:
            datos_ordenados[clave] = diccionarios[clave]
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(datos_ordenados, f, ensure_ascii=False, indent=2)


def actualizar_indices(archivo='indices.json'):
    try:
        diccionarios = leer_archivo_indices(archivo)
        ultimo_mes = obtener_ultimo_mes(diccionarios['haberes_minimos'])
        siguiente_mes = obtener_siguiente_mes(ultimo_mes)

        print(f"Último mes disponible: {ultimo_mes}")
        print(f"Nuevo mes a agregar: {siguiente_mes}")

        while True:
            try:
                indice = (
                    float(input("Ingrese el índice de actualización (ej: 2.08): ")))/100 + 1
                break
            except ValueError:
                print("Por favor, ingrese un número válido.")

        print(f"\nAplicando índice de actualización: {indice}")
        print("="*50)

        for nombre_dict in ['pbus', 'haberes_minimos', 'haberes_maximos', 'bases_maximas']:
            valor_anterior = diccionarios[nombre_dict][ultimo_mes]
            nuevo_valor = round(valor_anterior * indice, 2)
            diccionarios[nombre_dict][siguiente_mes] = nuevo_valor
            print(f"{nombre_dict.upper()}: {nuevo_valor}")

        print("-"*50)

        valor_actual_ucap = diccionarios.get('ucap', 0)
        nuevo_ucap = round(valor_actual_ucap * indice, 2)
        print(f"UCAP calculado: {nuevo_ucap}")
        respuesta_ucap = input("¿Es correcto el UCAP? (Enter = aceptar, o ingrese nuevo valor): ").strip()
        if respuesta_ucap:
            try:
                nuevo_ucap = float(respuesta_ucap)
                print(f"UCAP modificado: {nuevo_ucap}")
            except ValueError:
                print("Valor inválido, se conserva el calculado.")
        diccionarios['ucap'] = nuevo_ucap

        print("-"*50)
        print("RENTAS DE REFERENCIA")
        print("="*50)

        categorias_con_divisor = [
            'A', 'B', 'B2', 'C', 'C2', 'D', 'D2', 'E', 'E2', 'F',
            'G', 'G2', 'H', 'I (ex)', 'J', 'I2', 'II2', 'III2', 'IV2', 'V2'
        ]
        categorias_sin_divisor = ['I', 'II', 'III', 'IV', 'V']
        orden_rentas = categorias_sin_divisor + categorias_con_divisor

        rentas_nuevas = {}
        for cat in orden_rentas:
            if cat not in diccionarios['rentas_de_referencia']:
                continue
            serie = diccionarios['rentas_de_referencia'][cat]
            ultimo_fecha_renta = obtener_ultimo_mes(serie)
            ultimo_valor_renta = serie[ultimo_fecha_renta]
            nuevo_valor_renta = round(ultimo_valor_renta * indice, 2)

            if cat in categorias_con_divisor:
                valor_para_mostrar = round(nuevo_valor_renta * 0.32, 2)
                rentas_nuevas[cat] = {
                    'valor_real': nuevo_valor_renta,
                    'valor_mostrar': valor_para_mostrar,
                    'con_divisor': True
                }
            else:
                rentas_nuevas[cat] = {
                    'valor_real': nuevo_valor_renta,
                    'valor_mostrar': nuevo_valor_renta,
                    'con_divisor': False
                }

        print("\nCategorías I-V (valor tal cual):")
        for cat in categorias_sin_divisor:
            if cat in rentas_nuevas:
                print(f"  {cat:>5}: {rentas_nuevas[cat]['valor_mostrar']:>15.2f}")

        print("\nCategorías con factor 0.32 (valor mostrado / real entre paréntesis):")
        for cat in categorias_con_divisor:
            if cat in rentas_nuevas:
                r = rentas_nuevas[cat]
                print(f"  {cat:>8}: {r['valor_mostrar']:>15.2f}  (real: {r['valor_real']:>15.2f})")

        print("\n" + "="*50)
        respuesta_rentas = input("¿Los datos de rentas de referencia son correctos? (s/n): ").strip().lower()

        if respuesta_rentas == 'n':
            print("\nMODO EDICIÓN - Ingrese los nuevos valores (Enter para mantener el calculado):")
            print("(Para categorías con factor 0.32, ingrese el valor mostrado)")
            print("-"*50)

            for cat in orden_rentas:
                if cat not in rentas_nuevas:
                    continue
                r = rentas_nuevas[cat]
                if r['con_divisor']:
                    prompt = f"  {cat} (mostrado: {r['valor_mostrar']:.2f}): "
                else:
                    prompt = f"  {cat} (calculado: {r['valor_mostrar']:.2f}): "

                respuesta = input(prompt).strip()
                if respuesta:
                    try:
                        valor_editado = float(respuesta)
                        if r['con_divisor']:
                            rentas_nuevas[cat]['valor_real'] = round(valor_editado / 0.32, 2)
                            rentas_nuevas[cat]['valor_mostrar'] = valor_editado
                        else:
                            rentas_nuevas[cat]['valor_real'] = valor_editado
                            rentas_nuevas[cat]['valor_mostrar'] = valor_editado
                    except ValueError:
                        print(f"    Valor inválido, se mantiene el calculado.")

            print("\nValores finales guardados:")
            for cat in orden_rentas:
                if cat in rentas_nuevas:
                    r = rentas_nuevas[cat]
                    print(f"  {cat:>8}: {r['valor_real']:>15.2f}")

        for cat in rentas_nuevas:
            if cat not in diccionarios['rentas_de_referencia']:
                diccionarios['rentas_de_referencia'][cat] = {}
            diccionarios['rentas_de_referencia'][cat][siguiente_mes] = rentas_nuevas[cat]['valor_real']

        diccionarios['movilidad'][siguiente_mes] = round((indice-1)*100, 2)

        if siguiente_mes not in diccionarios['coeficientes_de_actualizacion']:
            proximos_3_meses = obtener_proximos_3_meses(ultimo_mes)
            print(
                f"\nCoeficientes de actualización faltantes para: {', '.join(proximos_3_meses)}")
            while True:
                try:
                    coeficiente = float(
                        input("Ingrese el coeficiente de actualización para estos 3 meses: "))
                    break
                except ValueError:
                    print("Por favor, ingrese un número válido.")

            print("COEFICIENTES_DE_ACTUALIZACION:")
            for mes in proximos_3_meses:
                diccionarios['coeficientes_de_actualizacion'][mes] = coeficiente
                print(f"  {mes}: {coeficiente}")
        else:
            print(
                f"\nCOEFICIENTES_DE_ACTUALIZACION: Ya existe para {siguiente_mes}")

        valor_actual_mono = diccionarios.get('monotributo_promovido', 'no definido')
        nuevo_mono = input(f"\nMonotributo promovido actual: {valor_actual_mono}\nIngrese nuevo monto (o Enter para mantener): ").strip()
        if nuevo_mono:
            try:
                diccionarios['monotributo_promovido'] = float(nuevo_mono)
                print(f"MONOTRIBUTO_PROMOVIDO: {nuevo_mono}")
            except ValueError:
                print("Valor inválido, se conserva el monto anterior.")
        else:
            print("MONOTRIBUTO_PROMOVIDO: sin cambios")

        print("="*50)
        escribir_archivo_indices(diccionarios, archivo)
        print(
            f"Archivo {archivo} actualizado exitosamente con los valores para {siguiente_mes}")

    except FileNotFoundError:
        print("Error: No se encontró el archivo indices.json")
    except Exception as e:
        print(f"Error: {str(e)}")


def calcular_movilidad():
    diccionarios = leer_archivo_indices()
    fechas = []
    importes = []
    for key, value in diccionarios["haberes_minimos"].items():
        importes.append(value)
        fechas.append(key[3:]+key[:2])
    fechas.sort()
    importes.sort()
    i = 0
    resultado = {}
    while i < len(importes)-1:
        porcentaje = round(((importes[i+1]/importes[i])-1)*100, 2)
        fecha_ok = fechas[i+1][4:] + "/" + fechas[i+1][:4]
        resultado[fecha_ok] = porcentaje
        i += 1
    diccionarios["movilidad"] = resultado
    escribir_archivo_indices(diccionarios)


def chequear_data():
    diccionarios = leer_archivo_indices()
    j = 0
    for greatKey, indice in diccionarios.items():
        print(greatKey)
        fechas = []
        importes = []
        if j == 4:
            j += 1
            continue
        if j == 5:
            for k, v in indice.items():
                print(k)
                fechas_renta = []
                importes_renta = []
                for key_renta, value_renta in v.items():
                    importes_renta.append(value_renta)
                    fechas_renta.append(key_renta[3:]+key_renta[:2])
                fechas_renta.sort()
                importes_renta.sort()
                h = 0
                for fecha in fechas_renta:
                    ok = fecha[4:] + "/" + fecha[:4]
                    if indice[k][ok] != importes_renta[h]:
                        print(k, " => ", ok, "!= ", importes_renta[h])
                    h += 1
            break
        if j >= 6:
            j += 1
            continue
        for key, value in indice.items():
            importes.append(value)
            fechas.append(key[3:]+key[:2])
        fechas.sort()
        importes.sort()
        i = 0
        for fecha in fechas:
            ok = fecha[4:] + "/" + fecha[:4]
            if indice[ok] != importes[i]:
                print(greatKey, " => ", ok, "!= ", importes[i])
            i += 1
        j += 1


if __name__ == "__main__":
    # En caso de querer utilizar un archivo de prueba poner de argumento en la funcion actualizar_indices un string con el nombre del archivo, pj '.indices-copia.json' #
    actualizar_indices()

    # chequear_data()
    # calcular_movilidad()
