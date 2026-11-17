import com.zeroc.Ice.Communicator;
import com.zeroc.Ice.Current;
import com.zeroc.Ice.ObjectAdapter;
import com.zeroc.Ice.Util;
import java.util.Locale;

public class Servidor {
    private static class PrinterI implements Demo.Printer {
        public String printString(String texto, Current current) {
            System.out.println(texto);
            return texto + "*";
        }

        public int soma(int a, int b, Current current) {
            return a + b;
        }

        public String maiuscula(String texto, Current current) {
            return texto.toUpperCase(Locale.ROOT);
        }
    }

    public static void main(String[] args) {
        String host = args.length > 0 ? args[0] : "0.0.0.0";
        try (Communicator comunicador = Util.initialize()) {
            ObjectAdapter adaptador = comunicador.createObjectAdapterWithEndpoints(
                "PrinterAdapter", "tcp -h " + host + " -p 5008");
            adaptador.add(new PrinterI(), Util.stringToIdentity("SimplePrinter"));
            adaptador.activate();
            System.out.println("Servidor Java em " + host + ":5008");
            comunicador.waitForShutdown();
        }
    }
}
