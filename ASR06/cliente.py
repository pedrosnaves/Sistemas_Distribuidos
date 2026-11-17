import sys
import Ice

Ice.loadSlice(["Printer.ice"])
import Demo


host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
with Ice.initialize() as comunicador:
    base = comunicador.stringToProxy(f"SimplePrinter:tcp -h {host} -p 5006")
    printer = Demo.PrinterPrx.checkedCast(base)
    if not printer:
        raise RuntimeError("Objeto remoto não encontrado")
    print("printString:", printer.printString("Hello World!"))
    print("soma:", printer.soma(10, 20))
    print("maiuscula:", printer.maiuscula("sistemas distribuídos"))
