# Env´ıa un paquete con loss_rate porcentaje de p´erdida

# si loss_rate = 5, implica un 5% de p´erdida

import random

import sys

import jsockets

import time

import socket


# Revisar si x está en la ventana:
def between(x, min, max):      # min <= x < max
    if min <= max:
        return (min <= x and x < max)
    else:
       return (min <= x or x < max)




def send_loss(s, data):

    global loss_rate



    if random.random() * 100 > loss_rate:



        s.send(data)



    else:



        print("[send_loss]")











def recv_loss(s, size):

    global loss_rate
    try:
        while True:
            data = s.recv(size)
            if random.random() * 100 <= loss_rate:
                print("[recv_loss]")
            else:
                break
    except socket.timeout:
        print("timeout", file=sys.stderr)
        data = None
    except socket.error:
        print("recv err", file=sys.stderr)
        data = None
    return data







if len(sys.argv) != 8:# Si el archivo se llama con menos o más de 8 parámetros



    print('Use: '+sys.argv[0]+'pack_sz nbytes timeout loss fileout host port')#imprime un error



    sys.exit(1)#Termina



#Si se llamó correctamente



s = jsockets.socket_udp_connect(sys.argv[6], sys.argv[7])#Se conecta al socket udp desde el hos en el puerto port







if s is None:#si no se conectó al socket



    print('could not open socket')#imprime un error



    sys.exit(1)#Termina







errores_fuera = 0
errores_dentro = 0



tamanho_paquete = sys.argv[1]



print("propuse paquete: " + tamanho_paquete + "\n")



nbytes = sys.argv[2]



timeout = sys.argv[3]



loss_rate = int(sys.argv[4])



archivo_out = sys.argv[5]



primer_envio = 'C' + tamanho_paquete.zfill(4) + timeout.zfill(4)



#Debo enviar una array de bytes que comience con la letra C, le sigue el tamaño del paquete propuesto y luego el valor del timeout



s.settimeout(3)



for i in range(100):



    send_loss(s, primer_envio.encode('UTF-8'))



    primera_respuesta = recv_loss(s, 5)





    if primera_respuesta:



        break







if not primera_respuesta:



    sys.exit(1)











#Voy a recibir del servidor una respuesta en un bytearray que comienza con la letra C (si no error) y le sigue el tamaño del paquete aceptado(no necesariamente el mismo que el propuesto)



primera_respuesta = primera_respuesta.decode()



tamanho_permitido = int(primera_respuesta[1:]) +3 #+3 porque son la primera letra más los números de paquete



print("recibo paquete: " + str(tamanho_permitido) + "\n")



#Luego el cliente envía la cantidad de bytes totales a enviar



segundo_envio = "N" + str(nbytes)

for i in range(100):


    
    send_loss(s, segundo_envio.encode('UTF-8'))

    print("se mando")

    segunda_respuesta = recv_loss(s, tamanho_permitido)
    if segunda_respuesta:



        break



if not segunda_respuesta:

    sys.exit(1)






print("recibiendo " + str(nbytes) + " nbytes" + "\n")



tiempo_inicio = time.time()#empieza el tiempo



numero_esperado = "00"#Número del paquete que debería llegar, empezamos con el 00

int_esperado = int(numero_esperado)


ultimo_recibido = "00"#Último número del paquete recibido

errores = 0#número de erroes



ventana_recepcion = [0]*50



numero_bytes=0

termino = True


recibido_decodeado = segunda_respuesta.decode()
posicion = int(recibido_decodeado[1:3])
if int_esperado == int(recibido_decodeado[1:3]):
    mensaje = "A" + numero_esperado#Mensaje de respuesta para confirmar la recepción

    send_loss(s, mensaje.encode('UTF-8'))#Mando el mensaje de confirmación

    with open(archivo_out, 'ab') as f:#Escribo en el archivo

         f.write(segunda_respuesta[3:])
         numero_bytes+=len(segunda_respuesta[3:])
    ultimo_recibido = numero_esperado
    int_esperado = (int_esperado + 1)%100
    numero_esperado = str(int_esperado).zfill(2)
elif between(posicion, int_esperado, (int_esperado + 50) % 100):
    errores_dentro+=1
    ventana_recepcion[posicion] = segunda_respuesta[3:]
    mensaje = "a" + recibido_decodeado[1:3]
    send_loss(s, mensaje.encode('UTF-8'))
    



while termino:

    recibido = recv_loss(s, tamanho_permitido)#Mensaje recibido del servidor
    

    if not recibido:#Si no recibo el mensaje

        sys.exit(1)#Aborto el programa

    
    recibido_decodeado = recibido.decode()
    posicion = int(recibido_decodeado[1:3])
    if numero_esperado == recibido_decodeado[1:3] :#Si el número esperado coincide con el recibido
        mensaje = "A" + numero_esperado#Mensaje de respuesta para confirmar la recepción

        send_loss(s, mensaje.encode('UTF-8'))#Mando el mensaje de confirmación

        ventana_recepcion[0]=recibido[3:]
        i = 0

        for j in range(50):
            if ventana_recepcion[j] == 0:
                break

            else:
                if ventana_recepcion[j] == "E" or recibido_decodeado[0] == "E":#Si la letra recibida es una E termina el proceso
                    termino = False
                else:
                    with open(archivo_out, 'ab') as f:#Escribo en el archivo

                        f.write(ventana_recepcion[j])
                        numero_bytes+=len(ventana_recepcion[j])
                        i+=1
            
        if i == 50:
            ventana_recepcion = [0]*50
        else:
            ventana_recepcion = ventana_recepcion[i:] + [0]*i
        ultimo_recibido = (str((int_esperado + i -1) %100)).zfill(2)
        int_esperado = (int_esperado+i)%100
        numero_esperado = str(int_esperado).zfill(2)
        
    


    elif between(posicion, int_esperado, (int_esperado + 50) % 100):
        errores_dentro +=1
        if(posicion < int_esperado):
            posicion_relativa = (posicion + 100 - int_esperado)%50
        else:
            posicion_relativa = (posicion-int_esperado)%50
        if ventana_recepcion[posicion_relativa] != 0:#ya me había llegado
            mensaje = "A" + ultimo_recibido
            print("ya me había llegado")
            send_loss(s,mensaje.encode('UTF-8'))#Vuelvo a enviar el último que recibí
        else:
            if recibido.decode()[0] == "E":#Si la letra recibida es una E termina el proceso
                ventana_recepcion[posicion_relativa] = 'E'
                print("llegó el paquete final")
            else:
                ventana_recepcion[posicion_relativa] = recibido[3:]

            mensaje = "a" + recibido_decodeado[1:3]
            send_loss(s, mensaje.encode('UTF-8'))

    else:#Si el paquete está fuera de la ventana

        errores_fuera+=1#Cuento el error    

        mensaje = "A" + ultimo_recibido

        send_loss(s,mensaje.encode('UTF-8'))#Vuelvo a enviar el último que recibí





tiempo_termino = time.time()

print("bytes recibidos " + str(numero_bytes) + ",")

tiempo_total = tiempo_termino-tiempo_inicio

print("time=" + str(tiempo_total) + ",")

ancho_banda = (numero_bytes/(1024*1024))/tiempo_total

print("bw=" + str(ancho_banda) + "MBytes/s" + "\n")

print("errores descarte de paquete " + str(errores_fuera))

print("errores desorden " + str(errores_dentro))

s.close()   
