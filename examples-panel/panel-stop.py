import holoviews as hv
import panel as pn
from panel.viewable import Viewer
import random
import pandas as pd
import time

from gizmo import Gizmo, Dag, Connection
import param

hv.extension('bokeh', inline=True)
pn.extension(nthreads=2, inline=True)
# hv.renderer('bokeh').theme = 'dark_minimal'

class QueryWidget(Gizmo):
    """A plain Python gizmo that accepts a "query" (a maximum count value) and outputs a dataframe."""

    timer_out = param.Integer(default=10)

    def __panel__(self):
        int_input = pn.widgets.IntInput(name='Timer period', value=5, step=1, start=1, end=10)
        button = pn.widgets.Button(name='OK', button_type='primary', align='end')

        def on_button(event):
            self.timer_out = int_input.value

        pn.bind(on_button, button, watch=True)

        return pn.Card(pn.Row(int_input, button), title=self.name, sizing_mode='stretch_width')

class ProgressWidget(Gizmo):
    timer_in = param.Integer()
    timer_out = param.Integer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress = pn.indicators.Progress(name='Progress', value=0, max=self.timer_in)

    def execute(self, stopper):
        self.value = 0
        self.progress.max = self.timer_in
        for t in range(1, self.timer_in+1):
            time.sleep(1)
            self.progress.value = t

            if stopper.is_stopped:
                return

        self.timer_out = self.timer_in

    def __panel__(self):
        return pn.Card(self.progress, title=self.name, sizing_mode='stretch_width')

def main():
    title = 'Stop Start'

    template = pn.template.MaterialTemplate(
        title=title,
        theme='dark',
        site='PoC ',
        sidebar=pn.Column('## Gizmos'),
        collapsed_sidebar=True
    )

    q = QueryWidget(name='Specify timer interval')
    b1 = ProgressWidget(name='Progress1')
    b2 = ProgressWidget(name='Progress2')

    dag = Dag()
    dag.connect(q, b1, Connection('timer_out', 'timer_in'))
    dag.connect(b1, b2, Connection('timer_out', 'timer_in'))

    # import json
    # with open('dag.json', 'w', encoding='utf-8') as f:
    #     json.dump(dag.dump(), f, indent=2)

    switch = pn.widgets.Switch(name='Stop / Start')

    def on_switch(event):
        if switch.value:
            dag.stop()
        else:
            dag.unstop()

    pn.bind(on_switch, switch, watch=True)

    template.main.objects = [pn.Column(q, b1, b2)]
    template.sidebar.objects = [
        pn.Column(
            switch,
            pn.panel(dag.hv_graph().opts(invert_yaxis=True, xaxis=None, yaxis=None))
        )
    ]
    template.show(threaded=False)

if __name__=='__main__':
    main()

