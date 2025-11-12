package example;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;


public class CalculatorTest {


    @Test
    public void generatedSmokeTest() throws Exception {

        Calculator subject = new Calculator();

        subject.add(0, 1);

        subject.subtract(0, 1);

        subject.divide(0, 1);

    }

}
