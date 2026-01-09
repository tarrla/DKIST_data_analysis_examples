from matplotlib.gridspec import GridSpec
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib osx
import warnings
from matplotlib.backend_bases import MouseButton

class ValidationError(Exception):
    pass

class ValidationWarning(UserWarning):
    pass



class BlittedCursor:
    """
    A cross-hair cursor using blitting for faster redraw.
    Adapted from https://matplotlib.org/stable/gallery/event_handling/cursor_demo.html#faster-redrawing-using-blitting
    """
    def __init__(self, ax, **kwargs):
        self.ax = ax
        self.title = ax.get_title()
        self.arraydata = ax.images[0].get_array()
        self.ny, self.nx = self.arraydata.shape
        self.lowerax = ax.figure.axes[2]
        self.rightax = ax.figure.axes[1]
        self.rightax.grid(True,ls=':')
        self.lowerax.grid(True,ls=':')
        
        self.background = None
        self.horizontal_line = ax.axhline(color='k', lw=0.8, ls='--')
        self.vertical_line = ax.axvline(color='k', lw=0.8, ls='--')
        self.rightline = self.rightax.plot(self.arraydata[:,0],np.arange(self.ny))[0]
        self.lowerline = self.lowerax.plot(np.arange(self.nx),self.arraydata[0,:])[0]
        self.rh_line = self.rightax.axhline(color='k', lw=0.8, ls='--')
        self.lv_line = self.lowerax.axvline(color='k', lw=0.8, ls='--')
        
        self.rightline.set_visible(False)
        self.lowerline.set_visible(False)
        self.rh_line.set_visible(False)
        self.lv_line.set_visible(False)
        self.horizontal_line.set_visible(False)
        self.vertical_line.set_visible(False)

        
        # text location in axes coordinates
        self.text = ax.text(0.02, 0.98, '',
                            transform=ax.transAxes,
                            bbox=dict(facecolor='white', alpha=0.5),
                            va = 'top')
        #self.text = ax.figure.text(0.7, 0.1, '')
        self._creating_background = False
        ax.figure.canvas.mpl_connect('draw_event', self.on_draw)
        self.rightax.set_ylim(0,self.ny-1)
        self.lowerax.set_xlim(0,self.nx-1)

        default_lim = np.array((np.min(self.arraydata),np.max(self.arraydata)))

        self.rightaxis_lim = kwargs.get('rightaxis_lim',default_lim)
        self.loweraxis_lim = kwargs.get('loweraxis_lim',default_lim)
        self.rightax.set_xlim(self.rightaxis_lim)
        self.lowerax.set_ylim(self.loweraxis_lim)

        # instruction text
        instruct_text = "Left click: redraw (after resize)"
        self.ax.figure.text(0.7,0.2,instruct_text)

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        self.rightline.set_visible(visible)
        self.lowerline.set_visible(visible)
        self.rh_line.set_visible(visible)
        self.lv_line.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.rightax.figure.canvas.draw()
        self.lowerax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)

        #also create backgrounds for the right and lower axes
        self.right_background = self.rightax.figure.canvas.copy_from_bbox(self.rightax.bbox)
        self.lower_background = self.lowerax.figure.canvas.copy_from_bbox(self.lowerax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_click(self,event):
        if event.button is MouseButton.LEFT:
            print('Redraw the backgorund')
            self.create_new_background()

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
                #right axes:
                self.rightax.figure.canvas.restore_region(self.right_background)
                self.rightax.figure.canvas.blit(self.rightax.bbox)
                # lower axes
                self.lowerax.figure.canvas.restore_region(self.lower_background)
                self.lowerax.figure.canvas.blit(self.lowerax.bbox)

        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            x, y = event.xdata, event.ydata
            val = self.arraydata[round(y),round(x)]
            ny,nx = self.arraydata.shape
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])
            self.rh_line.set_ydata([y])
            self.lv_line.set_xdata([x])
            self.text.set_text(f'x={x:1.2f}, y={y:1.2f}, I(x,y)={val:6.4E}')
            #self.ax.set_title(f'x={x:1.2f}, y={y:1.2f}, val={val:6.4E}')

            # side boxes:
            self.rightline.set_data([self.arraydata[:,round(x)],self.rightline.get_data()[1]] )
            self.lowerline.set_data([self.lowerline.get_data()[0],self.arraydata[round(y),:]] )

            
            self.ax.figure.canvas.restore_region(self.background)
            self.rightax.figure.canvas.restore_region(self.right_background)
            self.lowerax.figure.canvas.restore_region(self.lower_background)
            self.ax.draw_artist(self.horizontal_line)
            self.ax.draw_artist(self.vertical_line)
            self.ax.draw_artist(self.text)
            self.rightax.draw_artist(self.rightline)
            self.lowerax.draw_artist(self.lowerline)
            self.rightax.draw_artist(self.rh_line)
            self.lowerax.draw_artist(self.lv_line)
            
            self.ax.figure.canvas.blit(self.ax.bbox)
            self.rightax.figure.canvas.blit(self.rightax.bbox)
            self.lowerax.figure.canvas.blit(self.lowerax.bbox)
            


def simple_example():
    x = np.arange(0, 1, 0.01)
    y = np.sin(2 * 2 * np.pi * x)
    xx, yy = np.meshgrid(x,y)
    the_data = np.sin(xx)*np.cos(yy)
    ny,nx = the_data.shape
    
    fig = plt.figure(figsize=(9,8.5))
    gs = GridSpec(2, 2, width_ratios=[3, 1], height_ratios=[4, 1])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    
    #ax1.set_title('Blitted cursor')
    
    im = ax1.imshow(the_data,origin='lower',aspect='auto')
    
    blitted_cursor = BlittedCursor(ax1)
    fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)
    fig.canvas.mpl_connect('button_press_event', blitted_cursor.on_click)
    return fig, blitted_cursor
    
if __name__ =="__main__":
    print('Run in interactive mode:')
    print('> import updated_image_blitted_cursor as ub')
    print('# change the matplotlib backend, if necessary:')
    print('> %matplotlib osx')
    print('> fig, bc = ub.simple_example()')

#cid = fig.canvas.mpl_connect('motion_notify_event', mouse_move)
#cid = fig.canvas.mpl_connect('motion_notify_event', mouse_move)

# Simulate a mouse move to (0.5, 0.5), needed for online docs
#t = ax1.transData
#MouseEvent(
#    "motion_notify_event", ax.figure.canvas, *t.transform((0.5, 0.5))
#)._process()
