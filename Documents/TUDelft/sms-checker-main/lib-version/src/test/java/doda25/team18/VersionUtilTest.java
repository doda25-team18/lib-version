package doda25.team18;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Unit test for VersionUtil.
 */
public class VersionUtilTest {

    /**
     * Rigorous Test :-)
     */
    @Test
    public void testGetVersion() {
        String version = VersionUtil.getVersion();
        assertNotNull(version, "Version should not be null");
        assertEquals("1.0.0", version, "Version should match the one in pom.xml");
    }
}