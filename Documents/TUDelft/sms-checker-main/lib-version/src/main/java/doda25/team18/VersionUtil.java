package doda25.team18;

import java.io.InputStream;
import java.util.Properties;

public class VersionUtil {
    private static final String PATH = "/META-INF/maven/doda25-team18/lib-version/pom.properties";
    private static String version;

    static {
        try (InputStream input = VersionUtil.class.getResourceAsStream(PATH)) {
            if (input == null) {
                version = "unknown";
            } else {
                Properties prop = new Properties();
                prop.load(input);
                version = prop.getProperty("version", "unknown");
            }
        } catch (Exception ex) {
            ex.printStackTrace();
            version = "error";
        }
    }

    public static String getVersion() {
        return version;
    }

    // Main method for quick testing
    public static void main(String[] args) {
        System.out.println("Project version: " + getVersion());
    }
}
