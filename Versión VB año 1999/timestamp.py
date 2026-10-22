import pefile
import datetime

def obtener_timestamp_exe(ruta_archivo):
    try:
        # Cargar el archivo PE
        pe = pefile.PE(ruta_archivo)
        
        # Extraer el timestamp (segundos desde la época Unix)
        timestamp = pe.FILE_HEADER.TimeDateStamp
        
        # Convertir a fecha legible (UTC)
        fecha_compilacion = datetime.datetime.utcfromtimestamp(timestamp)
        
        print(f"Timestamp (raw): {timestamp}")
        print(f"Fecha de compilación (UTC): {fecha_compilacion}")
        
        pe.close()
        return fecha_compilacion
        
    except pefile.PEFormatError:
        print("Error: El archivo no es un ejecutable PE válido.")
    except Exception as e:
        print(f"Error inesperado: {e}")

# Ejemplo de uso
obtener_timestamp_exe("La casa encantada.exe")