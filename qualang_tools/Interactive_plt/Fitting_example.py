from Fitting import *

### Simulating the measured data ###
# Change x and y to be the measured data
k = 10
kc = 5
A = 10

x = np.linspace(-100, 100, 200)
y = (
    kc / 2 * ((k / 2) / (1 + (4 / k ** 2) * (x + 10) ** 2))
    + 1 * (np.random.rand(len(x)) - 0.5)
    + 200
)

### Fit ###
fit = Fitting()
# Choose the suitable fitting function
fit_function = fit.transmission_resonator_spectroscopy(x, y)
fit_params = dict(itertools.islice(fit_function.items(), 1, len(fit_function)))
yfit = fit_function["fit_func"](x)

### Plot ###
plt = Plot()
# Change xlablel and ylabel as needed
plt.plot(x, y, yfit, xlabel="frequency[Hz]", ylabel="transmission[a.u.]")

#### Save ###
save = Save()
# Save the file under the name written in file_name
file_name = "transmission"
save.save_params(x, y, fit_function, id=file_name)

### 0pen saved items ###
open = Open()
data = open.open_saved_params(f"data_fit_{file_name}.json")
open.print_params(data)
