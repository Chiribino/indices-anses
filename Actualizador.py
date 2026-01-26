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
        'bases_minimas': datos['bases_minimas'],
        'bases_maximas': datos['bases_maximas'],
        'coeficientes_de_actualizacion': datos['coeficientes_de_actualizacion'],
        'movilidad': datos['movilidad']
    }


def escribir_archivo_indices(diccionarios, archivo='indices.json'):
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(diccionarios, f, ensure_ascii=False, indent=2)


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

        for nombre_dict in ['pbus', 'haberes_minimos', 'haberes_maximos', 'bases_minimas', 'bases_maximas']:
            valor_anterior = diccionarios[nombre_dict][ultimo_mes]
            nuevo_valor = round(valor_anterior * indice, 2)
            diccionarios[nombre_dict][siguiente_mes] = nuevo_valor
            print(f"{nombre_dict.upper()}: {nuevo_valor}")

        diccionarios['rentas_de_referencia'] = {"A": 14.010264963437562,
                                                "B": 17.19884290019494,
                                                "B2": 18.81123349912165,
                                                "C": 25.146357885316064,
                                                "D": 34.39688507561582,
                                                "D2": 37.621590795314305,
                                                "E": 57.4336121222905,
                                                "E2": 62.81801038730368,
                                                "F": 80.33573208379138,
                                                "G": 114.82301701740326,
                                                "G2": 125.58767537554402,
                                                "H": 172.30211949550534,
                                                "I (ex)": 215.5464062175885,
                                                "J": 215.5464062175885,
                                                "I2": 19.646543676435257,
                                                "II2": 27.504738469341742,
                                                "III2": 39.292746060343866,
                                                "IV2": 62.86836416161999,
                                                "V2": 86.44365737866403,
                                                "I": 17.96255384340836,
                                                "II": 25.147188145020316,
                                                "III": 35.92479592922026,
                                                "IV": 57.47964723348114,
                                                "V": 79.0341999067812}

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
        if j == 5:
            j += 1
            continue
        if j == 6:
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
    # En caso de querer utilizar un archivo de prueba poner de argumento en la funcion actualizar_indices un string con el nombre del archivo, pj 'indices-copia.json' #
    actualizar_indices()

    # chequear_data()
    # calcular_movilidad()
