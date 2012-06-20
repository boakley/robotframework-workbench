'''GradientCanvas

This creates a canvas with a gradient background. The colors
of the gradient can be set with the set_colors method. The
axis can be set with set_axis, and must be "x" or "y". 

I'm not presently using this, but thought it might be useful
for tooltips or the window background or something.
'''
import Tkinter as tk

class GradientCanvas(tk.Canvas):
    '''A standard canvas widget with a gradient background'''
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self._color1 = "red"
        self._color2 = "black"
        self._axis = "x"
        self.bind("<Configure>", self._draw_gradient)

    def set_axis(self, axis):
        '''Set the axis along which the gradient should be drawn

        axis must be "x" or "y"
        '''
        if axis.lower() not in ("x","y"):
            raise Exception("axis must be 'x' or 'y'")
        self._axis = axis.lower()

    def set_colors(self, color1, color2):
        '''Set the colors used for the gradient'''
        self._color1 = color1
        self._color2 = color2
        
    def _draw_gradient(self, event=None):
        '''Draw the gradient
        
        N.B. this takes from 2-70ms to complete, depending on the
        size of the canvas
        '''
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()

        if self._axis == "x":
            limit = width
        else:
            limit = height

        (r1,g1,b1) = self.winfo_rgb(self._color1)
        (r2,g2,b2) = self.winfo_rgb(self._color2)
        r_ratio = float(r2-r1) / limit
        g_ratio = float(g2-g1) / limit
        b_ratio = float(b2-b1) / limit

        for i in range(limit):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))

            color = "#%4.4x%4.4x%4.4x" % (nr,ng,nb)
            if self._axis == "y":
                self.create_line(0,i,width,i,tags=("gradient",), fill=color)
            else:
                self.create_line(i,0,i,height, tags=("gradient",), fill=color)
        self.lower("gradient")

if __name__ == "__main__":
    root = tk.Tk()
    canvas1 = GradientCanvas(root, width=200, height=200)
    canvas1.pack(side="top", fill="both", expand=True)
    canvas1.set_axis("x")
    canvas1.set_colors("#ffffff", "#000000")

    canvas2 = GradientCanvas(root, width=200, height=200)
    canvas2.pack(side="top", fill="both", expand=True)
    canvas2.set_axis("y")
    canvas2.set_colors("red", "black")

    root.mainloop()
