import sys
import Ice

Ice.loadSlice(["Printer.ice"])
import Demo


class PrinterI(Demo.Printer):
    def printString(self, s, current=None):
        print(s, flush=True)
        return s + "*"

    def soma(self, a, b, current=None):
        return a + b

    def maiuscula(self, texto, current=None):
        return texto.upper()


host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
with Ice.initialize() as comunicador:
    adaptador = comunicador.createObjectAdapterWithEndpoints("PrinterAdapter", f"tcp -h {host} -p 5008")
    adaptador.add(PrinterI(), Ice.stringToIdentity("SimplePrinter"))
    adaptador.activate()
    print(f"Servidor Ice em {host}:5008", flush=True)
    comunicador.waitForShutdown()
