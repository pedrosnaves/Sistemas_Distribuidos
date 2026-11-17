import com.zeroc.Ice.Communicator;
import com.zeroc.Ice.Util;

public class Cliente {
    public static void main(String[] args) {
        String host = args.length > 0 ? args[0] : "127.0.0.1";
        try (Communicator comunicador = Util.initialize()) {
            Demo.PrinterPrx printer = Demo.PrinterPrx.checkedCast(
                comunicador.stringToProxy("SimplePrinter:tcp -h " + host + " -p 5008"));
            if (printer == null) {
                throw new IllegalStateException("Objeto remoto não encontrado");
            }
            System.out.println("printString: " + printer.printString("Hello World!"));
            System.out.println("soma: " + printer.soma(10, 20));
            System.out.println("maiuscula: " + printer.maiuscula("sistemas distribuídos"));
        }
    }
}
