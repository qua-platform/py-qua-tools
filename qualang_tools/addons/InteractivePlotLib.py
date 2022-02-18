import inspect
from scipy import optimize
import glob
from PIL import ImageGrab
from io import BytesIO
import os
import datetime
from IPython import get_ipython
import dill
import matplotlib.pyplot as plt
import numpy as np
import win32clipboard as clip
import win32con
from scipy.special import erf
import pandas as pd
import __main__ as _main_module


ipython = get_ipython()


class InteractivePlotLib:
    def __init__(self, doc_path=""):
        fig_numbers = plt.get_fignums()
        for i in fig_numbers:
            plt.close(plt.figure(i))
        self.figs = {}
        if doc_path:
            self.doc = Document(doc_path)
        else:
            self.doc = ""

    def garbage_collector(self):
        fig_numbers = plt.get_fignums()
        mark_to_delete = []
        for i in self.figs:
            if self.figs[i].fig.number not in fig_numbers:
                mark_to_delete.append(i)
        for i in mark_to_delete:
            del self.figs[i].fig
            del self.figs[i]

        for i in list(set(plt.get_fignums()) - set(self.figs.keys())):
            fig = plt.figure(i)
            self.figs[fig.number] = InteractivePlotLibFigure(fig, self.doc, self)

    def figure(self, ind=-1):
        self.garbage_collector()
        if ind in list(self.figs.keys()):
            self.figs[ind].fig.canvas.mpl_disconnect(self.figs[ind].cid)
            self.figs[ind].fig.canvas.mpl_disconnect(self.figs[ind].cid2)
            self.figs[ind].fig.canvas.mpl_disconnect(self.figs[ind].cid3)
        if ind < 0:
            fig = plt.figure()
        else:
            fig = plt.figure(ind)
        if len(fig.axes) == 0:
            plt.axes()
        self.figs[fig.number] = InteractivePlotLibFigure(fig, self.doc, self)
        return fig

    def load(self, number):
        pre_load_fig_numbers = plt.get_fignums()
        out = self.doc.load(number)
        self.garbage_collector()
        post_load_fig_numbers = plt.get_fignums()
        for i in list(set(post_load_fig_numbers) - set(pre_load_fig_numbers)):
            h = self.figure(i)
            for t in h.axes[0].texts:
                if len(t.get_text()) > 5 and t.get_text()[:5] == "Scan ":
                    t.remove()
            plt.show()
            plt.pause(1e-6)
        return out


class InteractivePlotLibFigure:
    def __init__(self, fig, doc, master_obj):

        self.fig = fig
        self.ax = self.fig.axes[0]
        self.doc = doc
        self.master_obj = master_obj

        self.line_selected = None
        self.th = 0.2
        self.th_point_advantage = 2

        self.correct_order = [0]

        self.marker_mode = False
        self.marker_list = [[]]

        self.grid_state = False

        self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        self.cid = self.fig.canvas.mpl_connect("button_press_event", self.mouse_click)
        self.cid2 = self.fig.canvas.mpl_connect("key_press_event", self.keyboard_click)
        self.cid3 = self.fig.canvas.mpl_connect(
            "key_release_event", self.keyboard_release
        )

        self.lines = []
        self.state = self.ProtoStateMachine(self, done=True)

    def user_interaction(self, type, event):
        self.refresh_axis()
        if self.state.done:
            if type == "mouse_click":
                xlim = self.ax.get_xlim()
                ylim = self.ax.get_ylim()
                bbox = self.ax.get_window_extent().transformed(  # axes bounding box
                    self.fig.dpi_scale_trans.inverted()
                )

                if event.y < bbox.ymin * self.fig.dpi:
                    if (
                        event.x
                        < (bbox.xmin + (bbox.xmax - bbox.xmin) / 5) * self.fig.dpi
                    ):
                        self.state = InteractivePlotLibFigure.StateMachineLim(
                            self, "xstart"
                        )
                    elif (
                        event.x
                        > (bbox.xmax - (bbox.xmax - bbox.xmin) / 5) * self.fig.dpi
                    ):
                        self.state = InteractivePlotLibFigure.StateMachineLim(
                            self, "xend"
                        )
                    else:
                        self.state = InteractivePlotLibFigure.StateMachineLabel(
                            self, "xlabel"
                        )

                elif event.y > bbox.ymax * self.fig.dpi:
                    self.state = InteractivePlotLibFigure.StateMachineLabel(
                        self, "title"
                    )

                elif event.x < bbox.xmin * self.fig.dpi:
                    if (
                        event.y
                        < (bbox.ymin + (bbox.ymax - bbox.ymin) / 5) * self.fig.dpi
                    ):
                        self.state = InteractivePlotLibFigure.StateMachineLim(
                            self, "ystart"
                        )
                    elif (
                        event.y
                        > (bbox.ymax - (bbox.ymax - bbox.ymin) / 5) * self.fig.dpi
                    ):
                        self.state = InteractivePlotLibFigure.StateMachineLim(
                            self, "yend"
                        )
                    else:
                        self.state = InteractivePlotLibFigure.StateMachineLabel(
                            self, "ylabel"
                        )

                elif event.x > bbox.xmax * self.fig.dpi:
                    self.state = InteractivePlotLibFigure.StateMachineLegend(self)

                else:
                    self.detect_curve_click(
                        event.xdata, event.ydata, xlim, ylim, bbox.width, bbox.height
                    )

            elif type == "keyboard_click":
                if event.key == "ctrl+v":
                    clip.OpenClipboard()
                    data = clip.GetClipboardData()
                    clip.CloseClipboard()

                    out = np.array(
                        ([i.split("\t") for i in data.split("\r\n")[:-1]]), "double"
                    )
                    self.ax.plot(out[:, 0], out[:, 1], linewidth=1)

                if event.key == "m":
                    self.marker_mode = not self.marker_mode

                if event.key == "M":
                    self.marker_list.append([])

                if event.key == "alt+m":
                    self.marker_list = [[]]
                    self.marker_mode = False

                if event.key == "f":
                    self.state = InteractivePlotLibFigure.StateMachineFit(self)

                if event.key == "g":
                    self.grid_state = not self.grid_state
                    self.ax.grid(self.grid_state)

                if event.key == "alt+f":
                    self.remove_fit()

                if event.key == "shift+s" or event.key == "S":
                    if self.doc.doc:
                        self.doc.doc(list(self.master_obj.figs.keys()))

                if event.key == "s":
                    if self.doc.doc:
                        self.doc.doc([plt.gcf().number])

                if self.line_selected:

                    if event.key == "c":
                        self.state = InteractivePlotLibFigure.StateMachineColor(self)

                    if event.key == "ctrl+c":
                        self.line_selected.copy_to_clipboard()

                    if event.key == "delete":
                        self.line_selected.delete()

                    if event.key == "up":
                        self.line_selected.correct_order(1)

                    if event.key == "down":
                        self.line_selected.correct_order(-1)

                    if event.key.isnumeric():
                        self.line_selected.line_width = int(event.key)
                        self.line_selected.emphasize_line_width()

            elif type == "keyboard_release":
                pass  # {"key": event.key}
        else:
            self.state.event(type, event)

        if self.state.done:
            self.state = self.ProtoStateMachine(self, done=True)

        self.refresh_figure()

    def detect_curve_click(self, base_x, base_y, base_xlim, base_ylim, width, height):
        scale_convert = InteractivePlotLibFigure.ConvertLogLin(
            [self.ax.get_xscale(), self.ax.get_yscale()]
        )
        line_list = self.get_lines_fit_extended()
        candidate = {"line_index": -1, "distance_2": np.inf, "xy": (0, 0)}
        x0 = scale_convert.convert[0](base_x)
        y0 = scale_convert.convert[1](base_y)
        xlim = scale_convert.convert[0](base_xlim)
        ylim = scale_convert.convert[1](base_ylim)

        xdiff = np.sqrt((xlim[1] - xlim[0]) ** 2 / width ** 2)
        ydiff = np.sqrt((ylim[1] - ylim[0]) ** 2 / height ** 2)

        for j, line in enumerate(line_list):
            x = scale_convert.bound[0](line.get_xdata())
            y = scale_convert.bound[1](line.get_ydata())
            idx = (
                (x >= base_xlim[0])
                & (x <= base_xlim[1])
                & (y >= base_ylim[0])
                & (y <= base_ylim[1])
            )
            idx = np.where(idx)[0]
            idx = list(set.union(set(idx), set(idx + 1), set(idx - 1)))
            idx = [i for i in idx if i >= 0 and i < len(x)]

            if len(idx) == 0:
                continue

            x = scale_convert.convert[0](x[idx])
            y = scale_convert.convert[1](y[idx])

            x_n = x / xdiff
            y_n = y / ydiff
            x0_n = x0 / xdiff
            y0_n = y0 / ydiff
            if line.get_linestyle() == "None":
                norm_2 = (
                    (x0_n - x_n) ** 2 + (y0_n - y_n) ** 2
                ) / self.th_point_advantage  # give advantage for choosing a point compared to a line
                ind = np.argmin(norm_2)
                if norm_2[ind] < candidate["distance_2"]:
                    candidate["line_index"] = j
                    candidate["distance_2"] = norm_2[ind]

                    candidate["xy"] = (
                        scale_convert.un_convert[0](x_n[ind] * xdiff),
                        scale_convert.un_convert[1](y_n[ind] * ydiff),
                    )
            else:
                for i in range(len(x_n) - 1):
                    d_2, x4, y4 = self.p4(
                        (x_n[i], y_n[i]), (x_n[i + 1], y_n[i + 1]), (x0_n, y0_n)
                    )

                    if d_2 < candidate["distance_2"]:
                        candidate["line_index"] = j
                        candidate["distance_2"] = d_2
                        candidate["xy"] = (
                            scale_convert.un_convert[0](x4 * xdiff),
                            scale_convert.un_convert[1](y4 * ydiff),
                        )

        self.line_selected = None  # deselect line if selected
        if candidate["distance_2"] < self.th ** 2:
            self.line_selected = InteractivePlotLibFigure.LineSelected(
                self,
                line_list[candidate["line_index"]],
                candidate["line_index"],
                candidate["xy"],
            )

    def remove_fit(self):
        lines = self.ax.get_lines()
        for line in lines:
            if hasattr(line, "InteractivePlotLib_Type") and (
                line.InteractivePlotLib_Type == "Fit"
                or line.InteractivePlotLib_Type == "Fit_markers"
            ):
                line.remove()

    def predefined_fit(self, req="g"):
        self.remove_fit()
        print(req)
        if req == "remove":
            return 0
        if req.isnumeric():
            Fit(int(req), self.ax)
        elif req == "g":
            Fit(lambda x: np.exp(-(x ** 2) / 2), self.ax)
        elif req == "e":
            Fit(lambda x: np.exp(x), self.ax)
        elif req == "l":
            Fit(lambda x: 1 / (1 + x ** 2), self.ax)
        elif req == "r":
            Fit(lambda x: erf(x), self.ax)
        elif req == "s":
            x = self.ax.get_lines()[0].get_xdata()
            y = self.ax.get_lines()[0].get_ydata()
            w = np.fft.fft(y)
            freqs = np.fft.fftfreq(len(x))
            new_f = freqs[1 : len(freqs // 2)]
            out_freq = new_f[np.argmax(np.abs(w[1 : len(freqs // 2)]))]
            omega = out_freq / np.mean(np.diff(x)) * 2 * np.pi
            xlim = self.ax.get_xlim()
            request_x_scale = 1 / omega / (xlim[1] - xlim[0])
            print(request_x_scale)
            Fit(lambda x: np.sin(x), self.ax, {"x_scale": request_x_scale})
        else:
            idx = req.find(",")
            convert_function = eval("lambda x,a: " + req[:idx])
            Fit(
                convert_function,
                self.ax,
                {
                    "initial_guess": eval(req[(idx + 1) :]),
                    "func": "lambda x,a: " + req[:idx],
                },
            )

    def p4(self, p1, p2, p3):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        dx, dy = x2 - x1, y2 - y1
        det = dx * dx + dy * dy
        if det == 0:
            return np.inf, 0, 0
        a = (dy * (y3 - y1) + dx * (x3 - x1)) / det
        if a < 0 or a > 1:
            return np.inf, 0, 0

        x4, y4 = x1 + a * dx, y1 + a * dy
        d_2 = (x4 - x3) ** 2 + (y4 - y3) ** 2
        return d_2, x4, y4

    class LineSelected:
        def __init__(self_line, sup_self, obj, line_index_selected, xy):
            self_line.sup_self = sup_self
            self_line.obj = obj
            self_line.line_index_selected = line_index_selected
            self_line.line_width = self_line.obj.get_linewidth()

            self_line.emphasize_line_width()
            self_line.alive = True
            self_line.click_xy = xy
            if sup_self.marker_mode:
                sup_self.marker_list[-1] = InteractivePlotLibFigure.Marker(
                    sup_self.ax, self_line.click_xy
                )

        def emphasize_line_width(self_line):
            if self_line.obj.get_linestyle() == "None":
                self_line.obj.set_marker("o")
            else:
                self_line.obj.set_linewidth(self_line.line_width + 1)

        def restore_line_width(self_line):
            if self_line.obj.get_linestyle() == "None":
                self_line.obj.set_marker(".")
            else:
                self_line.obj.set_linewidth(self_line.line_width)

        def copy_to_clipboard(self_line):
            data = ""
            x_list = self_line.obj.get_xdata()
            y_list = self_line.obj.get_ydata()
            for x, y in zip(x_list, y_list):
                data += f"{x}\t{y}\r\n"
            clip.OpenClipboard()
            clip.EmptyClipboard()
            clip.SetClipboardData(win32con.CF_UNICODETEXT, data)
            clip.CloseClipboard()

        def delete(self_line):
            self_line.obj.remove()
            self_line.alive = False

        def color(self_line, key):
            self_line.obj.set_color(key)

        def correct_order(self_line, change):

            sup_self = self_line.sup_self
            sup_self.check_zorder()
            local_order = sup_self.correct_order[self_line.line_index_selected]
            new_order = local_order + change

            if new_order > np.max(sup_self.correct_order) or new_order < np.min(
                sup_self.correct_order
            ):
                return
            # test
            local_idx = self_line.line_index_selected
            to_replace_idx = np.where(np.array(sup_self.correct_order) == new_order)[0]
            if len(to_replace_idx) == 1:
                sup_self.correct_order[local_idx] = new_order
                sup_self.correct_order[to_replace_idx[0]] = local_order
            sup_self.update_zorder()

        def __del__(self_line):
            if self_line.alive:
                self_line.restore_line_width()

    def check_zorder(self):
        self.lines = self.get_lines()
        while len(self.correct_order) < len(self.lines):
            self.correct_order.append(max(self.correct_order) + 1)

    def update_zorder(self):
        for i, line in enumerate(self.lines):
            line.set_zorder(self.correct_order[i] + 2.5)

        return 0

    def get_lines(self, compare_list=["Native"]):
        self.lines = []
        lines_list_raw = self.ax.get_lines()
        for line in lines_list_raw:
            if not hasattr(line, "InteractivePlotLib_Type"):
                setattr(line, "InteractivePlotLib_Type", "Native")
            for comp in compare_list:
                if line.InteractivePlotLib_Type == comp:
                    self.lines.append(line)
                    break

        return self.lines

    def get_lines_fit_extended(self):
        return self.get_lines(compare_list=["Native", "Fit_markers", "Fit"])

    class ConvertLogLin:
        def __init__(self_loglin, type_list):  # x,y
            self_loglin.convert = []
            self_loglin.un_convert = []
            self_loglin.bound = []
            for t in type_list:
                if t == "log":
                    self_loglin.convert.append(lambda x: np.log10(np.maximum(x, 1e-16)))
                    self_loglin.bound.append(lambda x: np.maximum(x, 1e-16))
                    self_loglin.un_convert.append(lambda x: 10 ** x)
                elif t == "linear":
                    self_loglin.convert.append(lambda x: x)
                    self_loglin.bound.append(lambda x: x)
                    self_loglin.un_convert.append(lambda x: x)
                else:
                    print("unknown scale")

    def refresh_axis(self):
        self.ax = plt.gca()

    def refresh_figure(self):
        self.fig.canvas.draw()

    def mouse_click(self, event):
        self.user_interaction("mouse_click", event)

    def keyboard_click(self, event):
        self.user_interaction("keyboard_click", event)

    def keyboard_release(self, event):
        self.user_interaction("keyboard_release", event)

    class ProtoStateMachine:
        def __init__(self_state, sup_self, done=False):
            self_state.done = done
            self_state.sup_self = sup_self

        def __del__(self_state):
            try:
                self_state.sup_self.refresh_figure()
            except BaseException:
                pass

    class StateMachineLegend(ProtoStateMachine):
        def __init__(self_state, sup_self):
            super().__init__(sup_self)
            self_state.legend = [""]
            self_state.lines = sup_self.get_lines()
            if sup_self.ax.get_legend():
                self_state.legend = [
                    i.get_text() for i in sup_self.ax.get_legend().texts
                ]
            self_state.legend_original = self_state.legend[:]
            self_state.index = 0
            self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                self_state.legend[self_state.index], self_state.update_legend
            )

        def event(self_state, type, event):
            if type == "keyboard_click":
                if event.key == "down":
                    if self_state.index < len(self_state.lines) - 1:
                        self_state.text_obj.done()
                        self_state.index += 1
                        if self_state.index >= len(self_state.legend):
                            self_state.legend.append("")
                        self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                            self_state.legend[self_state.index],
                            self_state.update_legend,
                        )

                elif event.key == "up":
                    if self_state.index > 0:
                        self_state.text_obj.done()
                        self_state.index -= 1
                        self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                            self_state.legend[self_state.index],
                            self_state.update_legend,
                        )

                else:
                    self_state.done = self_state.text_obj.react_to_key_press(event.key)

            elif type == "mouse_click":
                self_state.done = self_state.text_obj.done()
                self_state.sup_self.user_interaction("mouse_click", event)

        def update_legend(self_state, text):
            self_state.legend[self_state.index] = text
            self_state.sup_self.ax.legend(self_state.legend)

    class StateMachineLim(ProtoStateMachine):
        def __init__(self_state, sup_self, type="xlabel"):
            super().__init__(sup_self)
            self_state.type = type
            self_state.curser_location = 0
            self_state.command_stage = ""
            self_state.old_units = ""
            xlim = sup_self.ax.get_xlim()
            ylim = sup_self.ax.get_ylim()
            if type == "xstart":
                text = str(xlim[0])
                loc = [xlim[0], ylim[0]]
                va = "bottom"
                ha = "left"
            elif type == "xend":
                text = str(xlim[1])
                loc = [xlim[1], ylim[0]]
                va = "bottom"
                ha = "right"
            if type == "ystart":
                text = str(ylim[0])
                loc = [xlim[0], ylim[0]]
                va = "bottom"
                ha = "left"
            elif type == "yend":
                text = str(ylim[1])
                loc = [xlim[0], ylim[1]]
                va = "top"
                ha = "left"
            else:
                pass
            self_state.text_box = InteractivePlotLibFigure.TextObj(
                sup_self.ax, loc, text, ha=ha, va=va
            )
            self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                "", self_state.text_box.update_text, format_text=lambda x: x
            )

        def run_command(self_state, command, type):
            if self_state.command_stage == "unit_conversion":
                pass

        def event(self_state, type, event):
            if type == "keyboard_click":
                self_state.done = self_state.text_obj.react_to_key_press(event.key)

            elif type == "mouse_click":
                self_state.done = self_state.text_obj.done()
                self_state.sup_self.user_interaction("mouse_click", event)

            if self_state.done:
                xlim = self_state.sup_self.ax.get_xlim()
                ylim = self_state.sup_self.ax.get_ylim()
                try:
                    if self_state.type == "xstart":
                        self_state.sup_self.ax.set_xlim(
                            np.sort([float(self_state.text_obj.text), xlim[1]])
                        )
                    elif self_state.type == "xend":
                        self_state.sup_self.ax.set_xlim(
                            np.sort([xlim[0], float(self_state.text_obj.text)])
                        )
                    elif self_state.type == "ystart":
                        self_state.sup_self.ax.set_ylim(
                            np.sort([float(self_state.text_obj.text), ylim[1]])
                        )
                    elif self_state.type == "yend":
                        self_state.sup_self.ax.set_ylim(
                            np.sort([ylim[0], float(self_state.text_obj.text)])
                        )
                except BaseException:
                    pass

                self_state.text_box.remove()
                self_state.sup_self.refresh_figure()

    class StateMachineLabel(ProtoStateMachine):
        def __init__(self_state, sup_self, type="xlabel"):
            super().__init__(sup_self)
            self_state.type = type
            self_state.curser_location = 0
            self_state.command_stage = ""
            self_state.old_units = ""

            if type == "xlabel":
                text = sup_self.ax.get_xlabel()

                def set_label(t):
                    return sup_self.ax.set_xlabel(t)

            elif type == "ylabel":
                text = sup_self.ax.get_ylabel()

                def set_label(t):
                    return sup_self.ax.set_ylabel(t)

            elif type == "title":
                text = sup_self.ax.get_title()

                def set_label(t):
                    return sup_self.ax.set_title(t)

            text_help = "commands: \n:lin[ear]\n:log\n:u[nits]\n:[func]"
            self_state.help_box = InteractivePlotLibFigure.HelperText(
                self_state.sup_self.ax, text_help
            )

            self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                text, set_label, lambda x: x, lambda x: self_state.run_command(x, type)
            )

        def run_command(self_state, command, type):
            is_done = True
            if self_state.command_stage == "unit_conversion":
                # try:
                value_unit_split = self_state.text_obj.text.split("[")
                new_units = value_unit_split[1].split("]")[0]
                print(f"old:{self_state.old_units},new:{new_units}")
                convert_function = self_state.convert_units(
                    self_state.old_units, new_units
                )
                if type == "xlabel":
                    for line in self_state.sup_self.ax.get_lines():
                        line.set_xdata(convert_function(line.get_xdata()))
                    self_state.sup_self.ax.set_xlim(
                        convert_function(self_state.sup_self.ax.get_xlim())
                    )
                elif type == "ylabel":
                    for line in self_state.sup_self.ax.get_lines():
                        line.set_ydata(convert_function(line.get_ydata()))
                    self_state.sup_self.ax.set_ylim(
                        convert_function(self_state.sup_self.ax.get_ylim())
                    )
            else:
                if command == ":lin" or command == ":linear":
                    self_state.text_obj.text = self_state.text_obj.original_text
                    if type == "xlabel":
                        self_state.sup_self.ax.set_xscale("linear")
                    elif type == "ylabel":
                        self_state.sup_self.ax.set_yscale("linear")
                    self_state.text_obj.update_text()
                elif command == ":log":
                    self_state.text_obj.text = self_state.text_obj.original_text
                    if type == "xlabel":
                        self_state.sup_self.ax.set_xscale("log")
                    elif type == "ylabel":
                        self_state.sup_self.ax.set_yscale("log")
                    self_state.text_obj.update_text()
                elif command == ":u" or command == ":units":
                    try:
                        value_unit_split = self_state.text_obj.original_text.split("[")
                        self_state.old_units = value_unit_split[1].split("]")[0]
                        self_state.text_obj.text = value_unit_split[0] + "[]"
                        self_state.text_obj.curser_location = (
                            len(self_state.text_obj.text) - 1
                        )
                        self_state.text_obj.command_mode = True
                        self_state.text_obj.update_text()
                        self_state.command_stage = "unit_conversion"
                        is_done = False
                    except BaseException:
                        self_state.text_obj.text = self_state.text_obj.original_text
                        self_state.text_obj.update_text()
                        print("can't parse units - label should be 'Amplitude [mV]'")
                else:
                    try:

                        def convert_function(x):
                            return x

                        if type == "xlabel":
                            convert_function = eval("lambda x: " + command[1:])
                            for line in self_state.sup_self.ax.get_lines():
                                line.set_xdata(convert_function(line.get_xdata()))
                            self_state.sup_self.ax.set_xlim(
                                convert_function(
                                    np.array(self_state.sup_self.ax.get_xlim())
                                )
                            )

                        elif type == "ylabel":
                            convert_function = eval("lambda y: " + command[1:])
                            for line in self_state.sup_self.ax.get_lines():
                                line.set_ydata(convert_function(line.get_ydata()))
                            self_state.sup_self.ax.set_ylim(
                                convert_function(
                                    np.array(self_state.sup_self.ax.get_ylim())
                                )
                            )
                        self_state.text_obj.text = self_state.text_obj.original_text
                        self_state.text_obj.update_text()
                    except BaseException:
                        print("command not parsed")

            return is_done  # mark as done

        def event(self_state, type, event):
            if type == "keyboard_click":
                self_state.done = self_state.text_obj.react_to_key_press(event.key)

            elif type == "mouse_click":
                self_state.done = self_state.text_obj.done()
                self_state.sup_self.user_interaction("mouse_click", event)

            if self_state.done:
                self_state.help_box.remove()
                self_state.sup_self.refresh_figure()

        def convert_units(self, initial, final):

            if initial.lower() == "dbm":  # to Vp

                def to_SI(x):
                    return np.sqrt(50 / 1000) * (10 ** (x / 20)) * np.sqrt(2)

            elif initial[0] == "T":

                def to_SI(x):
                    return x * 1e12

            elif initial[0] == "G":

                def to_SI(x):
                    return x * 1e9

            elif initial[0] == "M":

                def to_SI(x):
                    return x * 1e6

            elif initial[0] == "K":

                def to_SI(x):
                    return x * 1e3

            elif initial[0] == "m":

                def to_SI(x):
                    return x * 1e-3

            elif initial[0] == "u":

                def to_SI(x):
                    return x * 1e-6

            elif initial[0] == "n":

                def to_SI(x):
                    return x * 1e-9

            elif initial[0] == "p":

                def to_SI(x):
                    return x * 1e-12

            elif initial[0] == "f":

                def to_SI(x):
                    return x * 1e-15

            elif initial[0] == "a":

                def to_SI(x):
                    return x * 1e-18

            else:

                def to_SI(x):
                    return x

            if "pp" in initial.lower():

                def to_SI2(x):
                    return to_SI(x / 2)

            elif "rms" in initial.lower():

                def to_SI2(x):
                    return to_SI(x * np.sqrt(2))

            else:
                to_SI2 = to_SI

            if final.lower() == "dbm":  # assuming Vp is input

                def from_SI(x):
                    return 10 * np.log10(((x / np.sqrt(2)) ** 2) * 1000 / 50)

            elif final[0] == "T":

                def from_SI(x):
                    return x * 1e-12

            elif final[0] == "G":

                def from_SI(x):
                    return x * 1e-9

            elif final[0] == "M":

                def from_SI(x):
                    return x * 1e-6

            elif final[0] == "K":

                def from_SI(x):
                    return x * 1e-3

            elif final[0] == "m":

                def from_SI(x):
                    return x * 1e3

            elif final[0] == "u":

                def from_SI(x):
                    return x * 1e6

            elif final[0] == "n":

                def from_SI(x):
                    return x * 1e9

            elif final[0] == "p":

                def from_SI(x):
                    return x * 1e12

            elif final[0] == "f":

                def from_SI(x):
                    return x * 1e15

            elif final[0] == "a":

                def from_SI(x):
                    return x * 1e18

            else:

                def from_SI(x):
                    return x

            if "pp" in final.lower():

                def from_SI2(x):
                    return from_SI(x * 2)

            elif "rms" in final.lower():

                def from_SI2(x):
                    return from_SI(x / np.sqrt(2))

            else:
                from_SI2 = from_SI

            return lambda x: from_SI2(to_SI2(np.array(x)))

    class StateMachineColor(ProtoStateMachine):
        def __init__(self_state, sup_self):
            super().__init__(sup_self)
            self_state.text_box = InteractivePlotLibFigure.CommandText(sup_self.ax)
            self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                "", self_state.text_box.update_text, format_text=lambda x: f"color: {x}"
            )

        def event(self_state, type, event):
            if type == "keyboard_click" or type == "mouse_click":
                self_state.done = self_state.text_obj.done()
                if type == "keyboard_click":
                    self_state.sup_self.line_selected.color(event.key)
                else:
                    self_state.sup_self.user_interaction("mouse_click", event)

    class StateMachineFit(ProtoStateMachine):
        def __init__(self_state, sup_self):
            super().__init__(sup_self)
            text = "x*a[0]+a[1],[1,1]\n"
            text += "# - polynom\n"
            text += "g - gaussian\n"
            text += "l - lorenzian\n"
            text += "e - exponent\n"
            text += "r - erf\n"
            text += "s - sine\n"

            self_state.text_box = InteractivePlotLibFigure.CommandText(sup_self.ax)
            self_state.text_obj = InteractivePlotLibFigure.InteractiveText(
                "",
                self_state.text_box.update_text,
                format_text=lambda x: f"Fit type: {x}",
            )
            self_state.help_box = InteractivePlotLibFigure.HelperText(
                self_state.sup_self.ax, text
            )

        def event(self_state, type, event):
            if type == "keyboard_click":
                self_state.done = self_state.text_obj.react_to_key_press(event.key)

            elif type == "mouse_click":
                self_state.done = self_state.text_obj.done()
                self_state.sup_self.user_interaction("mouse_click", event)

            if self_state.done:
                self_state.help_box.remove()
                print(self_state.text_obj.text)
                InteractivePlotLibFigure.predefined_fit(
                    self_state.sup_self, self_state.text_obj.text
                )
                self_state.sup_self.refresh_figure()

    class InteractiveText:
        # :
        def __init__(
            self_text,
            initial_text,
            update_text_fun,
            format_text=lambda x: x,
            command_func=lambda x: [],
        ):
            self_text.text = initial_text
            self_text.original_text = initial_text
            self_text.format_text = format_text
            self_text.update_text_fun = update_text_fun
            self_text.is_done = False
            self_text.curser_location = len(self_text.text)
            self_text.command_func = command_func
            self_text.update_text()
            self_text.first_key_stroke = True
            self_text.command_mode = False

        def update_text(self_text):
            buf = self_text.text
            if not self_text.is_done:
                buf = (
                    buf[: self_text.curser_location]
                    + "|"
                    + buf[self_text.curser_location :]
                )
            self_text.update_text_fun(self_text.format_text(buf))
            self_text.first_key_stroke = False

        def done(self_text):
            self_text.is_done = True
            self_text.update_text()
            return self_text.is_done

        def react_to_key_press(self_text, key):
            # print(self_text.first_key_stroke)
            if key == "enter":
                if (
                    len(self_text.text) > 0 and self_text.text[0] == ":"
                ) or self_text.command_mode:
                    is_done = self_text.command_func(self_text.text)
                    if is_done:
                        return self_text.done()
                    else:
                        return is_done  # =False

                return self_text.done()

            elif key == "escape":
                self_text.text = self_text.original_text
                return self_text.done()

            elif key == "backspace":
                if (len(self_text.text) > 0) and (self_text.curser_location > 0):
                    self_text.text = (
                        self_text.text[: self_text.curser_location - 1]
                        + self_text.text[self_text.curser_location :]
                    )
                    self_text.curser_location -= 1

            elif key == ":" and self_text.first_key_stroke:
                self_text.curser_location = 1
                self_text.text = ":"

            elif key == "delete":
                self_text.curser_location = 0
                self_text.text = ""

            elif key == "left":
                if self_text.curser_location > 0:
                    self_text.curser_location -= 1

            elif key == "right":
                if self_text.curser_location < len(self_text.text):
                    self_text.curser_location += 1

            elif len(key) == 1:
                self_text.text = (
                    self_text.text[: self_text.curser_location]
                    + key
                    + self_text.text[self_text.curser_location :]
                )
                self_text.curser_location += 1

            else:
                return self_text.is_done

            self_text.update_text()

            return self_text.is_done

    class TextObj:
        def __init__(self_textobj, ax, loc, text="", ha="left", va="top"):
            self_textobj.text_obj = ax.text(
                loc[0],
                loc[1],
                text,
                ha=ha,
                va=va,
            )

        def update_text(self_textobj, text):
            self_textobj.text_obj.set_text(text)

        def remove(self_textobj):
            self_textobj.text_obj.remove()

        def __del__(self_textobj):
            try:
                self_textobj.text_obj.remove()
            except BaseException:
                pass

    class CommandText(TextObj):
        def __init__(self, ax, text=""):
            super().__init__(ax, (min(ax.get_xlim()), max(ax.get_ylim())), text)

    class HelperText(TextObj):
        def __init__(self, ax, text=""):
            super().__init__(
                ax, (max(ax.get_xlim()), max(ax.get_ylim())), text, ha="right"
            )

    class Marker:
        def __init__(self_marker, ax, loc, text=""):
            if not text:
                x_text = (
                    f"{loc[0]:0.3f}"
                    if ((np.abs(loc[0]) > 1e-2) and (np.abs(loc[0]) < 1e2))
                    else f"{loc[0]:0.2e}"
                )
                y_text = (
                    f"{loc[1]:0.3f}"
                    if ((np.abs(loc[1]) > 1e-2) and (np.abs(loc[1]) < 1e2))
                    else f"{loc[1]:0.2e}"
                )
                text = f"[{x_text},{y_text}]"
            self_marker.text = InteractivePlotLibFigure.TextObj(
                ax, loc, text, "left", "bottom"
            )
            (self_marker.point,) = ax.plot(loc[0], loc[1], ".g")
            setattr(self_marker.point, "InteractivePlotLib_Type", "Marker")

        def __del__(self_marker):
            self_marker.point.remove()


class Document:
    def __init__(self, Data_path):
        self.Data_path = Data_path

    def doc(self, figs, unfiltered_variables=[], ignore=[]):
        print(figs)
        if not unfiltered_variables:
            unfiltered_variables = {}

            unfiltered_variables_module = _main_module

            att_list = dir(unfiltered_variables_module)

            for att in att_list:

                if att[0] == "_":
                    continue
                unfiltered_variables[att] = getattr(unfiltered_variables_module, att)

        self.ignore = ignore

        scan_number = self.save(unfiltered_variables)
        self.scan_number = scan_number
        print(type(figs))
        if type(figs) is list or type(figs) is np.ndarray:
            for fig in figs:
                self.save_fig(fig_number=fig, scan_number=scan_number)

        else:
            self.save_fig(fig_number=figs, scan_number=scan_number)

    def white_list(self, x, var):
        if x[0] == "_":
            return []
        if type(var) not in [
            np.ndarray,
            list,
            float,
            int,
            str,
            dict,
            complex,
            tuple,
        ]:
            return []
        if x in ["In", "Out", "exit", "get_ipython", "quit"]:
            return []
        if x in self.ignore:
            return []

        return x

    def get_variables(self, unfiltered_variables):
        out = []

        for x in sorted(unfiltered_variables.keys()):
            to_append = self.white_list(x, unfiltered_variables[x])
            if to_append:
                out.append(to_append)
        return out

    def get_last_scan_number(self):
        file_list = os.listdir(self.Data_path)

        if not file_list:
            scan_number = -1
        else:
            scans_list = [-1]
            for x in file_list:
                if "scan" in x:
                    scans_list.append(int(x.split("_")[0].split("scan")[1]))
            scan_number = max(scans_list)
        return scan_number

    def save(self, unfiltered_variables):

        Data_path = self.Data_path
        try:
            os.remove("./temp_code.txt")
        except BaseException:
            pass

        ipython.magic('history -n -f "./temp_code.txt"')
        f = open("./temp_code.txt", "r")
        code = f.read()
        f.close()

        scan_number = self.get_last_scan_number() + 1
        now = datetime.datetime.now()
        current_time = now.strftime("%Y_%m_%d_%H_%M_%S")
        info = {}
        variables = self.get_variables(unfiltered_variables)
        for variable in variables:
            info[variable] = unfiltered_variables[variable]
            if type(info[variable]) is list:
                for i in range(len(info[variable])):
                    if (
                        str(type(info[variable][i])).split("'")[1].split(".")[0]
                        == "matplotlib"
                    ):
                        info[variable][i] = []
        info["code"] = code
        dill.dump(
            info,
            open(
                (Data_path + "/scan{}_{}.dat").format(scan_number, current_time), "wb"
            ),
        )
        print(variables)
        return scan_number

    def load(self, n, load_figures=True):
        Data_path = self.Data_path

        if load_figures:

            try:

                figures_path = glob.glob(Data_path + "\\scan" + str(n) + "_*.pkl")
                for figure_path in figures_path:
                    dill.load(open(figure_path, "rb"))

            except BaseException:
                print("problem loading figures")

        data_path = glob.glob(Data_path + "\\scan" + str(n) + "_*.dat")
        if len(data_path) > 0:
            loaded_data = dill.load(open(data_path[0], "rb"))
        else:
            print("no such scan!")
            return 0

        print(loaded_data.keys())

        return loaded_data

    def save_fig(self, fig_number, scan_number=0):
        path = self.Data_path

        name = (
            "scan"
            + str(scan_number)
            + "_fig"
            + str(fig_number)
            + "_"
            + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        )
        path = os.path.join(path, name)

        h = plt.figure(fig_number)
        for t in h.axes[0].texts:
            if len(t.get_text()) > 5 and t.get_text()[:5] == "Scan ":

                t.remove()

        plt.text(
            plt.gca().get_xlim()[0],
            plt.gca().get_ylim()[1],
            "Scan " + str(self.scan_number),
            fontsize=12,
            va="top",
        )
        plt.pause(0.01)
        h.savefig(path + ".png")

        dill.dump(h, open(path + ".pkl", "wb"))

        self.generate_csv_data(h, path)

        image = ImageGrab.grab()
        output = BytesIO()
        mngr = plt.get_current_fig_manager()
        rect = mngr.window.geometry().getRect()
        image = image.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))

        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardData(win32con.CF_DIB, data)
        clip.CloseClipboard()
        # plt.pause(1)
        # r.remove()
        return path

    def generate_csv_data(self, fig, path):
        data = []
        ax = fig.get_axes()[0]
        for line in ax.get_lines():
            data.append({"x": line.get_xdata(), "y": line.get_ydata()})
        leg = ax.get_legend()
        if leg is not None:
            leg_names = []
            for t in ax.get_legend().get_texts():
                leg_names.append(t.get_text())
        else:
            leg_names = ["line " + str(i + 1) for i in range(len(data))]

        title = ax.get_title()
        if title == "":
            title = "untitled"

        xlabel = ax.get_xlabel()
        if xlabel == "":
            xlabel = "x"

        ylabel = ax.get_ylabel()
        if ylabel == "":
            ylabel = "y"

        all_x_data = [j for i in data for j in i["x"]]
        all_y_data = [j for i in data for j in i["y"]]
        all_leg_names = []

        for i in range(len(data)):
            if i < len(leg_names):
                all_leg_names += [leg_names[i]] * len(data[i]["x"])
            else:
                all_leg_names += [f"line {i}"] * len(data[i]["x"])
        df = pd.DataFrame(
            {
                "title": [title] * len(all_x_data),
                "legend": all_leg_names,
                xlabel: all_x_data,
                ylabel: all_y_data,
            }
        )
        df.to_csv(path + ".csv")


class Fit:
    def __init__(self, fit_type=1, ax=[], options={}):
        self.res = []
        if not ax:
            ax = plt.gca()
        self.ax = ax
        lines = self.ax.get_lines()
        if type(fit_type) == int:
            self.res = {
                "fit_type": [],
                "ax": [],
                "fit_func": [],
                "x": [],
                "y": [],
                "yf": [],
                "p": [],
                "y0": [],
                "x0": [],
                "dp": [],
                "dx0": [],
                "dy0": [],
                "ddp": [],
                "ddx0": [],
                "ddy0": [],
            }
        elif fit_type.__code__.co_argcount == 2:
            self.res = {
                "fit_type": [],
                "ax": [],
                "fit_func": [],
                "x": [],
                "y": [],
                "yf": [],
                "a": [],
                "func": [],
            }
        else:
            self.res = {
                "fit_type": [],
                "ax": [],
                "fit_func": [],
                "x": [],
                "y": [],
                "yf": [],
                "x_shift": [],
                "y_shift": [],
                "x_scale": [],
                "y_scale": [],
                "y_mid": [],
            }
        order_list = []
        for line in lines:
            order_list.append(line.zorder)
        idx = range(len(lines))
        for i in idx:
            if hasattr(lines[i], "InteractivePlotLib_Type") and (
                lines[i].InteractivePlotLib_Type == "Fit"
                or lines[i].InteractivePlotLib_Type == "Fit_markers"
                or lines[i].InteractivePlotLib_Type == "Marker"
            ):
                continue
            single_fit = SingleFit(lines[i], fit_type, ax, options)
            if not single_fit.ok:
                continue
            self.res["fit_type"].append(single_fit.fit_type)
            self.res["ax"].append(single_fit.ax)
            self.res["fit_func"].append(single_fit.fit_func)
            self.res["x"].append(single_fit.x)
            self.res["y"].append(single_fit.y)
            self.res["yf"].append(single_fit.yf)
            if type(fit_type) == int:
                self.res["p"].append(single_fit.p)
                self.res["y0"].append(single_fit.y0)
                self.res["x0"].append(single_fit.x0)
                self.res["dp"].append(single_fit.dp)
                self.res["dx0"].append(single_fit.dx0)
                self.res["dy0"].append(single_fit.dy0)
                self.res["ddp"].append(single_fit.ddp)
                self.res["ddx0"].append(single_fit.ddx0)
                self.res["ddy0"].append(single_fit.ddy0)
            elif fit_type.__code__.co_argcount == 2:
                self.res["a"].append(single_fit.popt)
                self.res["func"].append(options["func"])
            else:
                self.res["x_shift"].append(single_fit.x_shift)
                self.res["y_shift"].append(single_fit.y_shift)
                self.res["x_scale"].append(single_fit.x_scale)
                self.res["y_scale"].append(single_fit.y_scale)
                self.res["y_mid"].append(single_fit.y_mid)

            setattr(single_fit.fit_line_obj, "print", single_fit.text)
            setattr(single_fit.fit_line_obj, "fit_func", single_fit.fit_func)
            setattr(single_fit.fit_line_obj, "x_original", lines[i].get_xdata())
            setattr(single_fit.fit_line_obj, "y_original", lines[i].get_ydata())

        setattr(self.ax, "fit", self.res)
        setattr(_main_module, "fit", self.res)

    def __repr__(self):
        return str(self.res)


class SingleFit:
    def __init__(self, line, fit_type=1, ax=[], options={}):
        if not ax:
            ax = plt.gca()
        self.fit_type = fit_type
        self.ax = ax
        self.fit_func = lambda x: np.zeros_like(x)
        self.x = ([],)
        self.y = ([],)
        self.yf = ([],)
        self.x_shift = (0,)
        self.y_shift = (0,)
        self.x_scale = (1,)
        self.y_scale = (1,)
        self.y_mid = (0,)

        if callable(fit_type):

            if fit_type.__code__.co_argcount == 1:
                self.ok = self.fit_scaled_function(line, options)

            if fit_type.__code__.co_argcount == 2:
                x_data, y_data = self.get_xdata_ydata_from_axes(line)

                popt = curve_fit3(
                    lambda x, a: fit_type(x, a),
                    x_data,
                    y_data,
                    options["initial_guess"],
                )
                print(f"func = { options ['func'] }, a = {popt}")
                self.fit_func = lambda x: fit_type(x, popt)
                (l,) = plt.plot(x_data, self.fit_func(x_data), "m", linewidth=2)
                self.fit_line_obj = l
                setattr(self.fit_line_obj, "InteractivePlotLib_Type", "Fit")
                self.ok = True
                self.popt = popt
                self.text = f"a = {popt}"
                self.x = x_data
                self.y = y_data
                self.yf = self.fit_func(x_data)
            else:
                pass

        elif type(fit_type) == int:
            self.ok = self.fit_polygon(line, options)

        else:
            pass

    def get_xdata_ydata_from_axes(self, line):

        ax = self.ax

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        x_data = np.array(line.get_xdata())
        y_data = np.array(line.get_ydata())

        idx = (
            (x_data >= xlim[0])
            & (x_data <= xlim[1])
            & (y_data >= ylim[0])
            & (y_data <= ylim[1])
        )
        x_data = x_data[idx]
        y_data = y_data[idx]
        return x_data, y_data

    def plot_points_of_interest(self, points_of_interest_x, points_of_interest_y):

        xlim = plt.gca().get_xlim()
        ylim = plt.gca().get_ylim()
        (l2,) = plt.plot(points_of_interest_x, points_of_interest_y, ".r")
        self.fit_line_markers_obj = l2
        setattr(self.fit_line_markers_obj, "InteractivePlotLib_Type", "Fit_markers")
        setattr(
            self.fit_line_markers_obj,
            "InteractivePlotLib_Fit_Parent",
            self.fit_line_obj,
        )
        plt.gca().set_xlim(xlim)
        plt.gca().set_ylim(ylim)

    def fit_polygon(self, line, options):
        x_data, y_data = self.get_xdata_ydata_from_axes(line)
        if len(x_data) == 0:
            return False
        poly = np.polyfit(x_data, y_data, self.fit_type)
        self.p = poly
        self.fit_func = lambda x: np.polyval(poly, x)

        (l,) = plt.plot(x_data, self.fit_func(x_data), "m", linewidth=2)
        self.fit_line_obj = l
        setattr(self.fit_line_obj, "InteractivePlotLib_Type", "Fit")
        # self.parms = self.Fit_parms(
        self.x = x_data
        self.y = y_data
        self.yf = self.fit_func(x_data)
        self.y0 = self.fit_func(0)
        self.x0 = np.array(np.real([i for i in np.roots(poly) if np.isreal(i)]))
        self.dp = np.polyder(self.p)
        self.dx0 = np.array(np.real([i for i in np.roots(self.dp) if np.isreal(i)]))
        self.dy0 = [self.fit_func(i) for i in self.dx0]
        self.ddp = np.polyder(self.dp)
        self.ddx0 = np.array(np.real([i for i in np.roots(self.ddp) if np.isreal(i)]))
        self.ddy0 = [self.fit_func(i) for i in self.ddx0]
        points_of_interest_x = np.hstack([0, self.x0, self.dx0, self.ddx0])
        points_of_interest_y = np.hstack(
            [self.y0, [0] * len(self.x0), self.dy0, self.ddy0]
        )

        self.plot_points_of_interest(points_of_interest_x, points_of_interest_y)

        funcString = f"poly {self.fit_type}"
        text = f"func: {funcString}\n"

        text += "x0:"
        for i in self.x0:
            text += f"{i:2.2e},"
        text = text[:-1]
        text += f"\ny0:{self.y0}\n"
        if self.fit_type > 1:
            text += "d(x0,y0):"
            for dx0, dy0 in zip(self.dx0, self.dy0):
                text += f"({dx0:2.2e},{dy0:2.2e}),"
            text = text[:-1]

        if self.fit_type == 0:
            self.mean = poly[0]
            text += f"mean: {self.mean:2.2e}\n"

        if self.fit_type == 1:
            self.slope = poly[0]
            text += f"slope: {self.slope:2.2e}\n"

        self.text = text
        print(text)
        return True

    def fit_scaled_function(self, line, options):
        func = self.fit_type

        ax = self.ax

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_data, y_data = self.get_xdata_ydata_from_axes(line)
        if len(x_data) == 0:
            return False

        x_dummy = np.linspace(-np.pi / 2, np.pi / 2, 11)
        y_dummy = func(x_dummy)
        y_dummy_max = max(y_dummy)
        y_dummy_min = min(y_dummy)

        def scale_and_fit_function(f, x, shift_x, scale_x, shift_y, scale_y):
            return (f((x - shift_x) / scale_x) - shift_y) / scale_y

        shift_data_x = np.mean(xlim)
        shift_data_y = np.mean(ylim)

        scale_data_x = xlim[1] - xlim[0]
        scale_data_y = ylim[1] - ylim[0]

        scaled_x = (x_data - shift_data_x) / scale_data_x
        scaled_y = (y_data - shift_data_y) / scale_data_y

        mean_function = (y_dummy_max + y_dummy_min) / 2
        delta_function = y_dummy_max - y_dummy_min
        if "x_scale" in options:
            scaling_x_constant = options["x_scale"]
        else:
            scaling_x_constant = 0.1

        def R2(y, y_fit):
            ss_res = np.sum((y - y_fit) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / ss_tot)
            return r2

        def even_or_odd(func):
            y1 = func(1)
            y2 = func(-1)
            if y1 == y2:
                return "even"
            elif y1 == -y2:
                return "odd"
            else:
                return "other"

        function_symmetry_type = even_or_odd(func)
        if function_symmetry_type == "even":
            initial_guess = [
                [0, scaling_x_constant, mean_function, delta_function],
                [0, scaling_x_constant, mean_function, -delta_function],
            ]
        elif function_symmetry_type == "odd":
            initial_guess = [
                [0, scaling_x_constant, mean_function, delta_function],
                [0, -scaling_x_constant, mean_function, delta_function],
            ]
        else:
            initial_guess = [
                [0, scaling_x_constant, mean_function, delta_function],
                [0, -scaling_x_constant, mean_function, delta_function],
                [0, scaling_x_constant, mean_function, -delta_function],
                [0, -scaling_x_constant, mean_function, -delta_function],
            ]
        candidate_list = []
        for guess in initial_guess:
            popt = curve_fit2(
                lambda x, *args: scale_and_fit_function(func, x, *args),
                scaled_x,
                scaled_y,
                guess,
            )

            candidate_list.append(
                {
                    "popt": popt,
                    "R2": R2(scaled_y, scale_and_fit_function(func, scaled_x, *popt)),
                }
            )

        idx = np.argmin([1 - i["R2"] for i in candidate_list])
        popt = candidate_list[idx]["popt"]

        output = [
            popt[0] * scale_data_x + shift_data_x,
            popt[1] * scale_data_x,
            -(scale_data_y / (popt[3]) * popt[2] - shift_data_y),
            scale_data_y / popt[3],
        ]

        self.fit_func = (
            lambda x: func((x - output[0]) / output[1]) * output[3] + output[2]
        )
        (l,) = plt.plot(x_data, self.fit_func(x_data), "m", linewidth=2)
        self.fit_line_obj = l
        setattr(self.fit_line_obj, "InteractivePlotLib_Type", "Fit")
        # self.parms = self.Fit_parms(
        self.x = x_data
        self.y = y_data
        self.yf = self.fit_func(x_data)
        self.x_shift = output[0]
        self.y_shift = output[2]
        self.x_scale = output[1]
        self.y_scale = output[3]
        self.y_mid = self.fit_func(0)
        # )
        points_of_interest_x = np.hstack([self.x_shift, 0])
        points_of_interest_y = np.hstack(
            [self.fit_func(self.x_shift), self.fit_func(0)]
        )
        self.plot_points_of_interest(points_of_interest_x, points_of_interest_y)

        try:
            funcString = str(inspect.getsourcelines(func)[0])
            funcString = funcString.strip("['\\n']").split(" = ")[1]
            funcString = funcString.split(":")[1][1:]
        except BaseException:
            funcString = "?"

        text = f"func: {funcString}\n"
        text += f"→x:{self.x_shift:2.2e},↑y:{self.y_shift:2.2e}\n"
        text += f"↔x:{self.x_scale:2.2e},↕y:{self.y_scale:2.2e}\n"
        self.text = text
        print(text)
        return True


def curve_fit2(f, x, y, a0):
    def opt(x, y, a):
        return np.sum(np.abs(f(x, *a) - y) ** 2)

    out = optimize.minimize(lambda a: opt(x, y, a), a0)
    return out["x"]


def curve_fit3(f, x, y, a0):
    def opt(x, y, a):
        return np.sum(np.abs(f(x, a) - y) ** 2)

    out = optimize.minimize(lambda a: opt(x, y, a), a0)
    return out["x"]
