#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

double a, b, c, epsilon, delta;

double f(double x) {
    return x * x * x + a * x * x + b * x + c;
}

double fp(double x) {
    return 3 * x * x + 2 * a * x + b;
}

double fpp(double x) {
    return 6 * x + 2 * a;
}

int find_extremes(double *extreme_1, double *extreme_2) {
    double discriminant = 4 * (a * a - 3 * b);
    if (discriminant < -epsilon) {
        return 0;
    } else if (discriminant > epsilon) {
        double sqrt_d = sqrt(discriminant / 4);
        *extreme_1 = (-a - sqrt_d) / 3;
        *extreme_2 = (-a + sqrt_d) / 3;
        return 2;
    } else {
        *extreme_1 = -a / 3.0;
        *extreme_2 = *extreme_1;
        return 1;
    }
}

double find_border(double border_1, bool to_right) {
    double value_1 = f(border_1);
    double step = delta * (to_right ? 1 : -1);
    double border_2 = border_1 + step;
    int steps = 0;
    const int max_steps = 10000;
    while (value_1 * f(border_2) > 0 && steps < max_steps) {
        border_2 += step;
        steps++;
    }
    if (steps == max_steps) {
        fprintf(stderr, "Could not find border with sign change\n");
        exit(EXIT_FAILURE);
    }
    return border_2;
}

double dichotomy_method(double border_1, double border_2) {
    if (border_1 > border_2) {
        double temp = border_1;
        border_1 = border_2;
        border_2 = temp;
    }
    double f_1 = f(border_1);
    double f_2 = f(border_2);
    if (f_1 * f_2 > 0) {
        fprintf(stderr, "No sign change in dichotomy interval\n");
        exit(EXIT_FAILURE);
    }
    if (fabs(f_1) < epsilon) return border_1;
    if (fabs(f_2) < epsilon) return border_2;
    int iter = 0;
    const int max_iter = 1000;
    while (iter < max_iter) {
        double c = (border_1 + border_2) / 2;
        double f_c = f(c);
        if (fabs(f_c) < epsilon || fabs(border_2 - border_1) < epsilon) {
            return c;
        }
        if (f_1 * f_c < 0) {
            border_2 = c;
            f_2 = f_c;
        } else {
            border_1 = c;
            f_1 = f_c;
        }
        iter++;
    }
    fprintf(stderr, "Dichotomy reached max iterations, returning approximate\n");
    return (border_1 + border_2) / 2;
}

int find_roots(double *roots) {
    int res;
    double extreme_1, extreme_2;
    res = find_extremes(&extreme_1, &extreme_2);
    if (res == 0) {
        double border_1 = 0;
        double f_0 = f(border_1);
        if (fabs(f_0) < epsilon) {
            roots[0] = border_1;
            return 1;
        } else if (f_0 < -epsilon) {
            double border_2 = find_border(0, true);
            roots[0] = dichotomy_method(border_1, border_2);
            return 1;
        } else {
            double border_2 = find_border(0, false);
            roots[0] = dichotomy_method(border_2, border_1);
            return 1;
        }
    } else if (res == 1) {
        double extreme = extreme_1;
        double f_ext = f(extreme);
        if (fabs(f_ext) < epsilon) {
            roots[0] = extreme;
            return 1;
        } else if (f_ext >= epsilon) {
            double border_1 = find_border(extreme, false);
            roots[0] = dichotomy_method(border_1, extreme);
            return 1;
        } else {
            double border_2 = find_border(extreme, true);
            roots[0] = dichotomy_method(extreme, border_2);
            return 1;
        }
    } else {
        double f_1 = f(extreme_1);
        double f_2 = f(extreme_2);
        if (f_1 >= epsilon && f_2 >= epsilon) {
            double border_1 = find_border(extreme_1, false);
            roots[0] = dichotomy_method(border_1, extreme_1);
            return 1;
        } else if (f_1 <= -epsilon && f_2 <= -epsilon) {
            double border_2 = find_border(extreme_2, true);
            roots[0] = dichotomy_method(extreme_2, border_2);
            return 1;
        } else if (fabs(f_1) < epsilon && fabs(f_2) < epsilon) {
            roots[0] = (extreme_1 + extreme_2) / 2;
            return 1;
        } else if (f_1 >= epsilon && fabs(f_2) < epsilon) {
            double border_1 = find_border(extreme_1, false);
            roots[0] = dichotomy_method(border_1, extreme_1);
            roots[1] = extreme_2;
            return 2;
        } else if (fabs(f_1) < epsilon && f_2 <= -epsilon) {
            double border_2 = find_border(extreme_2, true);
            roots[0] = extreme_1;
            roots[1] = dichotomy_method(extreme_2, border_2);
            return 2;
        } else if (f_1 >= epsilon && f_2 <= -epsilon) {
            double border_1 = find_border(extreme_1, false);
            double border_2 = find_border(extreme_2, true);
            roots[0] = dichotomy_method(border_1, extreme_1);
            roots[1] = dichotomy_method(extreme_1, extreme_2);
            roots[2] = dichotomy_method(extreme_2, border_2);
            return 3;
        } else if (f_1 <= -epsilon && fabs(f_2) < epsilon) {
            double border_2 = find_border(extreme_2, true);
            roots[0] = dichotomy_method(extreme_1, extreme_2);
            roots[1] = extreme_2;
            return 2;
        } else if (fabs(f_1) < epsilon && f_2 >= epsilon) {
            double border_1 = find_border(extreme_1, false);
            roots[0] = extreme_1;
            roots[1] = dichotomy_method(extreme_1, border_1);
            return 2;
        }
    }
    return 0;
}

int main() {
    printf("Enter parameters a, b, c, delta, epsilon:\n");
    printf("a = ");
    scanf("%lf", &a);
    printf("b = ");
    scanf("%lf", &b);
    printf("c = ");
    scanf("%lf", &c);
    printf("delta = ");
    scanf("%lf", &delta);
    printf("epsilon = ");
    scanf("%lf", &epsilon);
    
    double roots[3];
    int root_count = find_roots(roots);
    
    printf("\nResults:\n");
    for (int i = 0; i < root_count; ++i) {
        double r = roots[i];
        int mult = 1;
        double fpr = fp(r);
        if (fabs(fpr) < epsilon) {
            mult = 2;
            double fppr = fpp(r);
            if (fabs(fppr) < epsilon) mult = 3;
        }
        printf("Root: %lf multiplicity: %d\n", r, mult);
    }
    return EXIT_SUCCESS;
}
