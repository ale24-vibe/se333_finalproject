package example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class CalculatorSpecTests {
    // Method under test: add
    @Test
    public void test_spec_equivalence_a_negative_0() {
        Calculator obj = new Calculator();
        assertEquals(-12, obj.add(-6, -6));
    }

    @Test
    public void test_spec_equivalence_a_zero_1() {
        Calculator obj = new Calculator();
        assertEquals(-6, obj.add(0, -6));
    }

    @Test
    public void test_spec_equivalence_a_positive_2() {
        Calculator obj = new Calculator();
        assertEquals(-1, obj.add(5, -6));
    }

    @Test
    public void test_spec_equivalence_b_negative_3() {
        Calculator obj = new Calculator();
        assertEquals(-12, obj.add(-6, -6));
    }

    @Test
    public void test_spec_equivalence_b_zero_4() {
        Calculator obj = new Calculator();
        assertEquals(-6, obj.add(-6, 0));
    }

    @Test
    public void test_spec_equivalence_b_positive_5() {
        Calculator obj = new Calculator();
        assertEquals(-1, obj.add(-6, 5));
    }

    @Test
    public void test_spec_boundary_a_6() {
        Calculator obj = new Calculator();
        assertEquals(-16, obj.add(-10, -6));
    }

    @Test
    public void test_spec_boundary_a_7() {
        Calculator obj = new Calculator();
        assertEquals(-15, obj.add(-9, -6));
    }

    @Test
    public void test_spec_boundary_a_8() {
        Calculator obj = new Calculator();
        assertEquals(3, obj.add(9, -6));
    }

    @Test
    public void test_spec_boundary_a_9() {
        Calculator obj = new Calculator();
        assertEquals(4, obj.add(10, -6));
    }

    @Test
    public void test_spec_boundary_a_10() {
        Calculator obj = new Calculator();
        assertEquals(-7, obj.add(-1, -6));
    }

    @Test
    public void test_spec_boundary_a_11() {
        Calculator obj = new Calculator();
        assertEquals(-6, obj.add(0, -6));
    }

    @Test
    public void test_spec_boundary_a_12() {
        Calculator obj = new Calculator();
        assertEquals(-5, obj.add(1, -6));
    }

    @Test
    public void test_spec_boundary_b_13() {
        Calculator obj = new Calculator();
        assertEquals(-16, obj.add(-6, -10));
    }

    @Test
    public void test_spec_boundary_b_14() {
        Calculator obj = new Calculator();
        assertEquals(-15, obj.add(-6, -9));
    }

    @Test
    public void test_spec_boundary_b_15() {
        Calculator obj = new Calculator();
        assertEquals(3, obj.add(-6, 9));
    }

    @Test
    public void test_spec_boundary_b_16() {
        Calculator obj = new Calculator();
        assertEquals(4, obj.add(-6, 10));
    }

    @Test
    public void test_spec_boundary_b_17() {
        Calculator obj = new Calculator();
        assertEquals(-7, obj.add(-6, -1));
    }

    @Test
    public void test_spec_boundary_b_18() {
        Calculator obj = new Calculator();
        assertEquals(-6, obj.add(-6, 0));
    }

    @Test
    public void test_spec_boundary_b_19() {
        Calculator obj = new Calculator();
        assertEquals(-5, obj.add(-6, 1));
    }

    @Test
    public void test_spec_boundary_combo_all_min_20() {
        Calculator obj = new Calculator();
        assertEquals(-20, obj.add(-10, -10));
    }

    @Test
    public void test_spec_boundary_combo_all_max_21() {
        Calculator obj = new Calculator();
        assertEquals(20, obj.add(10, 10));
    }

}
