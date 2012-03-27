import Tkinter as tk
class RobotTally(object):
    def __init__(self):
        self.var = {
            ("critical","pass"): tk.IntVar(0),
            ("critical","fail"): tk.IntVar(0),
            ("critical","total"): tk.IntVar(0),
            ("all","pass"): tk.IntVar(0),
            ("all","fail"): tk.IntVar(0),
            ("all","total"): tk.IntVar(0),
            ("warnings"): tk.IntVar(0),
            }

    def add_result(self, attrs):
        status = "pass" if attrs["status"].lower() == "pass" else "fail"
        if attrs["critical"] == "yes":
            value = self.var["critical", status].get()+1
            self.var["critical", status].set(value)
        value = self.var["all", status].get()+1
        self.var["all", status].set(value)

        self.var[("all","total")].set(self.var[("all","pass")].get() + self.var[("all","fail")].get())
        self.var["critical","total"].set(self.var["critical","pass"].get() + self.var["critical","fail"].get())

    def __getitem__(self, key):
        return self.var[key]

    def get(self, *keys):
        return self.var[keys].get()

    def __str__(self):
        (cpass, cfail, ctotal, apass, afail, atotal) = self.summary()
        critical = "%s critical tests, %s passed, %s failed." % (ctotal, cpass, cfail)
        total = "%s tests total, %s passed, %s failed." % (atotal, apass, afail)
        return critical + " " + total

    def summary(self):
        '''Return a summary of the test result

        This returns a list of 6 values in the following order:
        critical pass, critical fail, critical total, 
        all pass, all fail, all total
        '''
        
        return (self.var["critical","pass"].get(),
                self.var["critical","fail"].get(),
                self.var["critical","total"].get(),
                self.var["all","pass"].get(),
                self.var["all","fail"].get(),
                self.var["all","total"].get(),
#                self.var["warnings"].get(),
                )
