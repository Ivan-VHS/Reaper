# Orthogonal Metric Engine

Reaper exposes the Pythagorean family of models as pure, deterministic language built-ins and as a reusable Python module, reaper.metric_space. No filesystem, network, process, device or host capability is added by these operations.

## Built-ins

| Built-in | Meaning |
|---|---|
| metric_dot(a, b) | Inner product of equal-length numeric vectors |
| vector_norm(v) | Stable Euclidean norm in n dimensions |
| euclidean_distance(a, b) | Euclidean distance between equal-length vectors |
| is_orthogonal(a, b[, tolerance]) | Near-orthogonality check using normalized cosine magnitude |
| quadratic_form(v, matrix) | Evaluate v-transpose × matrix × v |
| law_of_cosines(a, b, angle_radians) | Recover the opposite side from two sides and the included angle |
| de_gua_area(a, b, c) | Hypotenuse-face area for a tri-rectangular tetrahedron |
| parseval_energy(coefficients) | Sum squared coefficients in a normalized orthogonal basis |
| unit_circle_residual(angle_radians) | Absolute numerical residual of sin² + cos² = 1 |
| spherical_hypotenuse(a, b) | Unit-sphere right-triangle hypotenuse; side inputs in radians |
| hyperbolic_hypotenuse(a, b) | Curvature -1 right-triangle hypotenuse |
| minkowski_interval(ct, spatial) | (ct)² - sum(spatial coordinate²), signature (+---) |
| combine_variances(values) | Sum variances only for uncorrelated components |
| reciprocal_altitude(a, b) | Right-triangle altitude from the reciprocal identity |

Vectors are Reaper lists of finite numbers. Boolean values are deliberately rejected as numbers. The maximum vector length is 4096; quadratic matrices are limited to 512 × 512. Equal dimensions and square matrices are enforced.

The variance combiner requires zero covariance. Independence is sufficient, but not necessary. Parseval energy assumes coefficients in a normalized orthogonal basis. A quadratic form is not automatically a distance: callers must use a symmetric positive-definite matrix when they need a metric.

## Example

Run examples/orthogonal_metrics.rpr with the Reaper interpreter to exercise the feature end-to-end.

## Mathematical scope

Euclidean distance, inner products, orthogonal projections and quadratic forms provide the shared core. Law of cosines generalizes side composition; de Gua extends the relation to perpendicular faces; Parseval carries it to orthogonal expansions; spherical and hyperbolic functions change the space's curvature; the Minkowski form changes the metric signature; and the variance and reciprocal-altitude rules preserve the same sum-of-squares structure under their stated assumptions.
