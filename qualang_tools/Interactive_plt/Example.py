from Fitting import *

k = 10
kc = 5
A = 10

x = np.linspace(-100, 100, 200)
y = kc / 2 * ((k / 2) / (1 + (4 / k ** 2) * (x + 10) ** 2)) + 1 * (np.random.rand(len(x)) - 0.5) + 200

# fitting
fit = Fitting()
fit_function = fit.transmitted_lorenzian(x, y)
fit_params = dict(itertools.islice(fit_function.items(), 1, len(fit_function)))
yfit = fit_function["fit_func"](x)

x = np.linspace(0, 100, 100)
y = 4 * (x + 5 * (np.random.rand(len(x)) - 0.5)) + 10

# plotting
plt = Plot()
plt.plot(x, y, yfit, xlabel='frequancy[MHz]', ylabel='transmission[a.u.]')

# saving
save = Save()
file_name = 'linear_data'
save.save_params(x, y, fit_function, id=file_name)

# open saved items
open = Open()
data = open.open_saved_params(f"data_fit_{file_name}.json")
open.print_params(data)
