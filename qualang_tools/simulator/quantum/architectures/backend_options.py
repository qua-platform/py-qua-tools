import jax

jax.config.update("jax_enable_x64", True)
jax.config.update("jax_platform_name", "cpu")

dt = 1 / 4.5e9

solver_options = {"method": "jax_odeint",
                  "atol": 1e-6,
                  "rtol": 1e-8,
                  "hmax": dt}
