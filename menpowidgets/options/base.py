from collections import OrderedDict
from functools import partial
import numpy as np

import ipywidgets
from traitlets import link

from menpowidgets.tools import (IndexButtonsWidget, IndexSliderWidget, 
                                LineOptionsWidget, MarkerOptionsWidget, 
                                ImageOptionsWidget, NumberingOptionsWidget, 
                                FigureOptionsOneScaleWidget, 
                                FigureOptionsTwoScalesWidget, 
                                LegendOptionsWidget, GridOptionsWidget, 
                                ColourSelectionWidget, HOGOptionsWidget, 
                                DaisyOptionsWidget, LBPOptionsWidget,  
                                IGOOptionsWidget, DSIFTOptionsWidget, 
                                SlicingCommandWidget, format_box, format_font,
                                convert_image_to_bytes, 
                                map_styles_to_hex_colours)


class ChannelOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for selecting channel options when rendering an image. The
    widget consists of the following parts from `IPython.html.widgets`:

    == ============== ================================== =======================
    No Object         Variable (`self.`)                 Description
    == ============== ================================== =======================
    1  RadioButtons   `mode_radiobuttons`                The mode selector

                                                         'Single' or 'Multiple'
    2  Checkbox       `masked_checkbox`                  Controls masked mode
    3  IntSlider      `single_slider`                    Single channel selector
    4  IntRangeSlider `multiple_slider`                  Channels range selector
    5  Checkbox       `rgb_checkbox`                     View as RGB
    6  Checkbox       `sum_checkbox`                     View sum of channels
    7  Checkbox       `glyph_checkbox`                   View glyph
    8  BoundedIntText `glyph_block_size_text`            Glyph block size
    9  Checkbox       `glyph_use_negative_checkbox`      Use negative values
    10 VBox           `glyph_options_box`                Contains 8, 9
    11 VBox           `glyph_box`                        Contains 7, 10
    12 HBox           `multiple_options_box`             Contains 6, 11, 5
    13 Box            `sliders_box`                      Contains 3, 4
    14 Box            `sliders_and_multiple_options_box` Contains 13, 12
    15 VBox           `mode_and_masked_box`              Contains 1, 2
    == ============== ================================== =======================

    Note that:

    * The selected values are stored in the ``self.selected_values`` `dict`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` method.

    Parameters
    ----------
    channel_options : `dict`
        The dictionary with the initial options. For example
        ::

            channel_options = {'n_channels': 10,
                               'image_is_masked': True,
                               'channels': 0,
                               'glyph_enabled': False,
                               'glyph_block_size': 3,
                               'glyph_use_negative': False,
                               'sum_enabled': False,
                               'masked_enabled': True}

    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create a channels widget and then update its state. Firstly, we need
    to import it:

        >>> from menpowidgets.options import ChannelOptionsWidget
        >>> from IPython.display import display

    Now let's define a render function that will get called on every widget
    change and will dynamically print the selected channels and masked flag:

        >>> from menpo.visualize import print_dynamic
        >>> def render_function(name, value):
        >>>     s = "Channels: {}, Masked: {}".format(
        >>>         wid.selected_values['channels'],
        >>>         wid.selected_values['masked_enabled'])
        >>>     print_dynamic(s)

    Create the widget with some initial options and display it:

        >>> channel_options = {'n_channels': 30,
        >>>                    'image_is_masked': True,
        >>>                    'channels': [0, 10],
        >>>                    'glyph_enabled': False,
        >>>                    'glyph_block_size': 3,
        >>>                    'glyph_use_negative': False,
        >>>                    'sum_enabled': True,
        >>>                    'masked_enabled': True}
        >>> wid = ChannelOptionsWidget(channel_options,
        >>>                            render_function=render_function,
        >>>                            style='warning')
        >>> display(wid)

    By playing around with the widget, printed message gets updated. Finally,
    let's change the widget status with a new dictionary of options:

        >>> new_options = {'n_channels': 10,
        >>>                'image_is_masked': True,
        >>>                'channels': [7, 8, 9],
        >>>                'glyph_enabled': True,
        >>>                'glyph_block_size': 3,
        >>>                'glyph_use_negative': True,
        >>>                'sum_enabled': False,
        >>>                'masked_enabled': False}
        >>> wid.set_widget_state(new_options, allow_callback=False)
    """
    def __init__(self, channel_options, render_function=None, style='minimal'):
        # If image_is_masked is False, then masked_enabled should be False too
        if not channel_options['image_is_masked']:
            channel_options['masked_enabled'] = False

        # Parse channels
        mode_default, single_slider_default, multiple_slider_default = \
            self._parse_options(channel_options['channels'])

        # Check sum and glyph options
        channel_options['sum_enabled'], channel_options['glyph_enabled'] = \
            self._parse_sum_glyph(mode_default, channel_options['sum_enabled'],
                                  channel_options['glyph_enabled'])

        # Create widgets
        self.mode_radiobuttons = ipywidgets.RadioButtons(
            options=['Single', 'Multiple'], value=mode_default,
            description='Mode:', disabled=channel_options['n_channels'] == 1)
        self.masked_checkbox = ipywidgets.Checkbox(
            value=channel_options['masked_enabled'], description='Masked',
            visible=channel_options['image_is_masked'])
        self.single_slider = ipywidgets.IntSlider(
            min=0, max=channel_options['n_channels']-1, step=1,
            value=single_slider_default, description='Channel',
            visible=self._single_slider_visible(mode_default),
            disabled=channel_options['n_channels'] == 1)
        self.multiple_slider = ipywidgets.IntRangeSlider(
            min=0, max=channel_options['n_channels']-1, step=1,
            value=multiple_slider_default, description='Channels',
            visible=self._multiple_slider_visible(mode_default))
        self.rgb_checkbox = ipywidgets.Checkbox(
            value=(channel_options['n_channels'] == 3 and
                   channel_options['channels'] is None),
            description='RGB',
            visible=self._rgb_checkbox_visible(
                mode_default, channel_options['n_channels']))
        self.sum_checkbox = ipywidgets.Checkbox(
            value=channel_options['sum_enabled'], description='Sum',
            visible=self._sum_checkbox_visible(
                mode_default, channel_options['n_channels']))
        self.glyph_checkbox = ipywidgets.Checkbox(
            value=channel_options['glyph_enabled'], description='Glyph',
            visible=self._glyph_checkbox_visible(
                mode_default, channel_options['n_channels']))
        self.glyph_block_size_text = ipywidgets.BoundedIntText(
            description='Block size', min=1, max=25,
            value=channel_options['glyph_block_size'], width='1.5cm')
        self.glyph_use_negative_checkbox = ipywidgets.Checkbox(
            description='Negative', value=channel_options['glyph_use_negative'])

        # Group widgets
        self.glyph_options_box = ipywidgets.VBox(
            children=[self.glyph_block_size_text,
                      self.glyph_use_negative_checkbox],
            visible=self._glyph_options_visible(
                mode_default, channel_options['n_channels'],
                channel_options['glyph_enabled']))
        self.glyph_box = ipywidgets.VBox(children=[self.glyph_checkbox,
                                                   self.glyph_options_box],
                                         align='start')
        self.multiple_options_box = ipywidgets.HBox(
            children=[self.sum_checkbox, self.glyph_box, self.rgb_checkbox])
        self.sliders_box = ipywidgets.Box(
            children=[self.single_slider, self.multiple_slider])
        self.sliders_and_multiple_options_box = ipywidgets.Box(
            children=[self.sliders_box, self.multiple_options_box])
        self.mode_and_masked_box = ipywidgets.VBox(
            children=[self.mode_radiobuttons, self.masked_checkbox])
        super(ChannelOptionsWidget, self).__init__(
            children=[self.mode_and_masked_box,
                      self.sliders_and_multiple_options_box])
        self.align = 'start'
        self.orientation = 'horizontal'

        # Assign output
        self.selected_values = channel_options

        # Set style
        self.predefined_style(style)

        # Set functionality
        def mode_selection(name, value):
            # Temporarily remove render function
            self.sum_checkbox.on_trait_change(self._render_function, 'value',
                                              remove=True)
            self.glyph_checkbox.on_trait_change(self._render_function, 'value',
                                                remove=True)
            # Control visibility of widgets
            if value == 'Single':
                self.multiple_slider.visible = False
                self.single_slider.visible = True
                self.sum_checkbox.visible = False
                self.sum_checkbox.value = False
                self.glyph_checkbox.visible = False
                self.glyph_checkbox.value = False
                self.glyph_options_box.visible = False
                self.rgb_checkbox.visible = \
                    self.selected_values['n_channels'] == 3
            else:
                self.single_slider.visible = False
                self.multiple_slider.visible = True
                self.sum_checkbox.visible = True
                self.sum_checkbox.value = False
                self.glyph_checkbox.visible = \
                    self.selected_values['n_channels'] > 1
                self.glyph_checkbox.value = False
                self.glyph_options_box.visible = False
                self.rgb_checkbox.visible = False
            # Add render function
            if self._render_function is not None:
                self.sum_checkbox.on_trait_change(self._render_function,
                                                  'value')
                self.glyph_checkbox.on_trait_change(self._render_function,
                                                    'value')
        self.mode_radiobuttons.on_trait_change(mode_selection, 'value')

        def glyph_options_visibility(name, value):
            # Temporarily remove render function
            self.sum_checkbox.on_trait_change(self._render_function, 'value',
                                              remove=True)
            # Check value of sum checkbox
            if value:
                self.sum_checkbox.value = False
            # Add render function
            if self._render_function is not None:
                self.sum_checkbox.on_trait_change(self._render_function,
                                                  'value')
            # Control glyph options visibility
            self.glyph_options_box.visible = value
        self.glyph_checkbox.on_trait_change(glyph_options_visibility, 'value')

        self.link_rgb_checkbox_and_single_slider = link(
            (self.rgb_checkbox, 'value'), (self.single_slider, 'disabled'))

        def sum_fun(name, value):
            # Temporarily remove render function
            self.glyph_checkbox.on_trait_change(self._render_function, 'value',
                                                remove=True)
            # Check value of glyph checkbox
            if value:
                self.glyph_checkbox.value = False
            # Add render function
            if self._render_function is not None:
                self.glyph_checkbox.on_trait_change(self._render_function,
                                                    'value')
        self.sum_checkbox.on_trait_change(sum_fun, 'value')

        def get_glyph_options(name, value):
            self.selected_values['glyph_enabled'] = self.glyph_checkbox.value
            self.selected_values['sum_enabled'] = self.sum_checkbox.value
            self.selected_values['glyph_use_negative'] = \
                self.glyph_use_negative_checkbox.value
            self.selected_values['glyph_block_size'] = \
                self.glyph_block_size_text.value
        self.glyph_checkbox.on_trait_change(get_glyph_options, 'value')
        self.sum_checkbox.on_trait_change(get_glyph_options, 'value')
        self.glyph_use_negative_checkbox.on_trait_change(get_glyph_options,
                                                         'value')
        self.glyph_block_size_text.on_trait_change(get_glyph_options, 'value')

        def get_channels(name, value):
            if self.mode_radiobuttons.value == "Single":
                if self.rgb_checkbox.value:
                    self.selected_values['channels'] = None
                else:
                    self.selected_values['channels'] = self.single_slider.value
            else:
                self.selected_values['channels'] = range(
                    self.multiple_slider.lower, self.multiple_slider.upper + 1)
        self.single_slider.on_trait_change(get_channels, 'value')
        self.multiple_slider.on_trait_change(get_channels, 'value')
        self.rgb_checkbox.on_trait_change(get_channels, 'value')
        self.mode_radiobuttons.on_trait_change(get_channels, 'value')

        def get_masked(name, value):
            self.selected_values['masked_enabled'] = value
        self.masked_checkbox.on_trait_change(get_masked, 'value')

        # Set render function
        self._render_function = None
        self.add_render_function(render_function)

    def _parse_options(self, channels):
        if isinstance(channels, list):
            if len(channels) == 1:
                mode_value = 'Single'
                single_slider_value = channels[0]
                multiple_slider_value = (0, 1)
            else:
                mode_value = 'Multiple'
                single_slider_value = 0
                multiple_slider_value = (min(channels), max(channels))
        elif channels is None:
            mode_value = 'Single'
            single_slider_value = 0
            multiple_slider_value = (0, 1)
        else:
            mode_value = 'Single'
            single_slider_value = channels
            multiple_slider_value = (0, 1)
        return mode_value, single_slider_value, multiple_slider_value

    def _parse_sum_glyph(self, mode_value, sum_enabled, glyph_enabled):
        if mode_value == 'Single' or (sum_enabled and glyph_enabled):
            sum_enabled = False
            glyph_enabled = False
        return sum_enabled, glyph_enabled

    def _single_slider_visible(self, mode):
        return mode == 'Single'

    def _multiple_slider_visible(self, mode):
        return mode == 'Multiple'

    def _rgb_checkbox_visible(self, mode, n_channels):
        return mode == 'Single' and n_channels == 3

    def _sum_checkbox_visible(self, mode, n_channels):
        return mode == 'Multiple' and n_channels > 1

    def _glyph_checkbox_visible(self, mode, n_channels):
        return mode == 'Multiple' and n_channels > 1

    def _glyph_options_visible(self, mode, n_channels, glyph_value):
        return mode == 'Multiple' and n_channels > 1 and glyph_value

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight='', slider_width='', slider_colour=None):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}

        slider_width : `str`, optional
            The width of the slider.
        slider_colour : `str`, optional
            The colour of the sliders.
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        self.single_slider.width = slider_width
        self.multiple_slider.width = slider_width
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.mode_radiobuttons, font_family, font_size, font_style,
                    font_weight)
        format_font(self.single_slider, font_family, font_size, font_style,
                    font_weight)
        format_font(self.multiple_slider, font_family, font_size, font_style,
                    font_weight)
        format_font(self.masked_checkbox, font_family, font_size, font_style,
                    font_weight)
        format_font(self.rgb_checkbox, font_family, font_size, font_style,
                    font_weight)
        format_font(self.sum_checkbox, font_family, font_size, font_style,
                    font_weight)
        format_font(self.glyph_checkbox, font_family, font_size, font_style,
                    font_weight)
        format_font(self.glyph_use_negative_checkbox, font_family, font_size,
                    font_style, font_weight)
        format_font(self.glyph_block_size_text, font_family, font_size,
                    font_style, font_weight)
        self.single_slider.slider_color = slider_colour
        self.single_slider.background_color = slider_colour
        self.multiple_slider.slider_color = slider_colour
        self.multiple_slider.background_color = slider_colour

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style=None, border_visible=True,
                       border_color='black', border_style='solid',
                       border_width=1, border_radius=0, padding='0.2cm',
                       margin='0.3cm', font_family='', font_size=None,
                       font_style='', font_weight='', slider_width='5cm',
                       slider_colour=None)
            format_box(self.glyph_options_box, box_style='',
                       border_visible=False, border_color='',
                       border_style='solid', border_width=1, border_radius=0,
                       padding='0.1cm', margin=0)
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       slider_width='5cm',
                       slider_colour=map_styles_to_hex_colours(style))
            format_box(self.glyph_options_box, box_style=style,
                       border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.1cm', margin=0)
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function = render_function
        if self._render_function is not None:
            self.mode_radiobuttons.on_trait_change(self._render_function,
                                                   'value')
            self.masked_checkbox.on_trait_change(self._render_function, 'value')
            self.single_slider.on_trait_change(self._render_function, 'value')
            self.multiple_slider.on_trait_change(self._render_function, 'value')
            self.rgb_checkbox.on_trait_change(self._render_function, 'value')
            self.sum_checkbox.on_trait_change(self._render_function, 'value')
            self.glyph_checkbox.on_trait_change(self._render_function, 'value')
            self.glyph_block_size_text.on_trait_change(self._render_function,
                                                       'value')
            self.glyph_use_negative_checkbox.on_trait_change(
                self._render_function, 'value')

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        self.mode_radiobuttons.on_trait_change(self._render_function, 'value',
                                               remove=True)
        self.masked_checkbox.on_trait_change(self._render_function, 'value',
                                             remove=True)
        self.single_slider.on_trait_change(self._render_function, 'value',
                                           remove=True)
        self.multiple_slider.on_trait_change(self._render_function, 'value',
                                             remove=True)
        self.rgb_checkbox.on_trait_change(self._render_function, 'value',
                                          remove=True)
        self.sum_checkbox.on_trait_change(self._render_function, 'value',
                                          remove=True)
        self.glyph_checkbox.on_trait_change(self._render_function, 'value',
                                            remove=True)
        self.glyph_block_size_text.on_trait_change(self._render_function,
                                                   'value', remove=True)
        self.glyph_use_negative_checkbox.on_trait_change(self._render_function,
                                                         'value', remove=True)
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)

    def set_widget_state(self, channel_options, allow_callback=True):
        r"""
        Method that updates the state of the widget with a new set of values.

        Parameters
        ----------
        channel_options : `dict`
            The dictionary with the new options to be used. For example
            ::

                channel_options = {'n_channels': 10,
                                   'image_is_masked': True,
                                   'channels': 0,
                                   'glyph_enabled': False,
                                   'glyph_block_size': 3,
                                   'glyph_use_negative': False,
                                   'sum_enabled': False,
                                   'masked_enabled': True}

        allow_callback : `bool`, optional
            If ``True``, it allows triggering of any callback functions.
        """
        # temporarily remove render callback
        render_function = self._render_function
        self.remove_render_function()

        # If image_is_masked is False, then masked_enabled should be False too
        if not channel_options['image_is_masked']:
            channel_options['masked_enabled'] = False

        # Parse channels
        mode_default, single_slider_default, multiple_slider_default = \
            self._parse_options(channel_options['channels'])

        # Check sum and glyph options
        channel_options['sum_enabled'], channel_options['glyph_enabled'] = \
            self._parse_sum_glyph(mode_default, channel_options['sum_enabled'],
                                  channel_options['glyph_enabled'])

        # Update widgets' state
        self.mode_radiobuttons.value = mode_default
        self.mode_radiobuttons.disabled = channel_options['n_channels'] == 1

        self.masked_checkbox.value = channel_options['masked_enabled']
        self.masked_checkbox.visible = channel_options['image_is_masked']

        self.single_slider.max = channel_options['n_channels'] - 1
        self.single_slider.value = single_slider_default
        self.single_slider.visible = self._single_slider_visible(mode_default)
        self.single_slider.disabled = channel_options['n_channels'] == 1

        self.multiple_slider.max = channel_options['n_channels'] - 1
        self.multiple_slider.value = multiple_slider_default
        self.multiple_slider.visible = self._multiple_slider_visible(
            mode_default)

        self.rgb_checkbox.value = (channel_options['n_channels'] == 3 and
                                   channel_options['channels'] is None)
        self.rgb_checkbox.visible = self._rgb_checkbox_visible(
            mode_default, channel_options['n_channels'])

        self.sum_checkbox.value = channel_options['sum_enabled']
        self.sum_checkbox.visible = self._sum_checkbox_visible(
            mode_default, channel_options['n_channels'])

        self.glyph_checkbox.value = channel_options['glyph_enabled']
        self.glyph_checkbox.visible = self._glyph_checkbox_visible(
            mode_default, channel_options['n_channels'])

        self.glyph_block_size_text.value = channel_options['glyph_block_size']

        self.glyph_use_negative_checkbox.value = \
            channel_options['glyph_use_negative']

        self.glyph_options_box.visible = self._glyph_options_visible(
            mode_default, channel_options['n_channels'],
            channel_options['glyph_enabled'])

        # Re-assign render callback
        self.add_render_function(render_function)

        # Assign new options dict to selected_values
        self.selected_values = channel_options

        # trigger render function if allowed
        if allow_callback:
            self._render_function('', True)


class LandmarkOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for animating through a list of objects. The widget
    consists of the following parts from `IPython.html.widgets`:

    == ============= ================================ ==========================
    No Object        Variable (`self.`)               Description
    == ============= ================================ ==========================
    1  Latex         `no_landmarks_msg`               Message in case there are

                                                      no landmarks available.
    2  Checkbox      `render_landmarks_checkbox`      Render landmarks
    3  Box           `landmarks_checkbox_and_msg_box` Contains 2, 1
    4  Dropdown      `group_dropdown`                 Landmark group selector
    5  ToggleButtons `labels_toggles`                 `list` of `lists` with

                                                      the labels per group
    6  Latex         `labels_text`                    Labels title text
    7  HBox          `labels_box`                     Contains all 5
    8  HBox          `labels_and_text_box`            Contains 6, 7
    9  VBox          `group_and_labels_and_text_box`  Contains 4, 8
    == ============= ================================ ==========================

    Note that:

    * The selected values are stored in the ``self.selected_values`` `dict`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` and ``replace_update_function()`` methods.

    Parameters
    ----------
    landmark_options : `dict`
        The dictionary with the initial options. For example
        ::

            landmark_options = {'has_landmarks': True,
                                'render_landmarks': True,
                                'group_keys': ['PTS', 'ibug_face_68'],
                                'labels_keys': [['all'], ['jaw', 'eye']],
                                'group': 'PTS',
                                'with_labels': ['all']}

    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    update_function : `function` or ``None``, optional
        The update function that is executed when the index value changes.
        If ``None``, then nothing is assigned.
    style : `str` (see below)
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create a landmarks widget and then update its state. Firstly, we need
    to import it:

        >>> from menpowidgets.options import LandmarkOptionsWidget
        >>> from IPython.display import display

    Now let's define a render function that will get called on every widget
    change and will dynamically print the selected index:

        >>> from menpo.visualize import print_dynamic
        >>> def render_function(name, value):
        >>>     s = "Group: {}, Labels: {}".format(
        >>>         wid.selected_values['group'],
        >>>         wid.selected_values['with_labels'])
        >>>     print_dynamic(s)

    Create the widget with some initial options and display it:

        >>> landmark_options = {'has_landmarks': True,
        >>>                     'render_landmarks': True,
        >>>                     'group_keys': ['PTS', 'ibug_face_68'],
        >>>                     'labels_keys': [['all'], ['jaw', 'eye', 'mouth']],
        >>>                     'group': 'ibug_face_68',
        >>>                     'with_labels': ['eye', 'jaw', 'mouth']}
        >>> wid = LandmarkOptionsWidget(landmark_options,
        >>>                              render_function=render_function,
        >>>                              style='danger')
        >>> display(wid)

    By playing around with the widget, the printed message gets updated.
    Finally, let's change the widget status with a new dictionary of options:

        >>> new_options = {'has_landmarks': True,
        >>>                'render_landmarks': True,
        >>>                'group_keys': ['new_group'],
        >>>                'labels_keys': [['1', '2', '3']],
        >>>                'group': 'new_group',
        >>>                'with_labels': None}
        >>> wid.set_widget_state(new_options, allow_callback=False)
    """
    def __init__(self, landmark_options, render_function=None,
                 update_function=None, style='minimal'):
        # Check given options
        landmark_options = self._parse_landmark_options_dict(landmark_options)

        # Temporarily store visible and disabled values
        tmp_visible = self._options_visible(landmark_options['has_landmarks'])
        tmp_disabled = not landmark_options['render_landmarks']
        tmp_slider_visible = self._group_slider_visible(
            landmark_options['group_keys'])
        # Get selected group value index
        group_idx = landmark_options['group_keys'].index(
            landmark_options['group'])

        # Create widgets
        # Render landmarks checkbox and no landmarks message
        self.no_landmarks_msg = ipywidgets.Latex(
            value='No landmarks available.',
            visible=self._no_landmarks_msg_visible(
                landmark_options['has_landmarks']))
        self.render_landmarks_checkbox = ipywidgets.Checkbox(
            description='Render landmarks',
            value=landmark_options['render_landmarks'], visible=tmp_visible)
        self.landmarks_checkbox_and_msg_box = ipywidgets.Box(
            children=[self.render_landmarks_checkbox, self.no_landmarks_msg])
        # Create group description, dropdown and slider
        self.group_description = ipywidgets.Latex(value='Group', margin='0.1cm')
        dropdown_dict = OrderedDict()
        for gn, gk in enumerate(landmark_options['group_keys']):
            dropdown_dict[gk] = gn
        self.group_slider = ipywidgets.IntSlider(
            min=0, max=len(landmark_options['group_keys']) - 1, margin='0.1cm',
            font_size=0, value=group_idx, disabled=tmp_disabled, width='3cm',
            visible=tmp_slider_visible)
        self.group_dropdown = ipywidgets.Dropdown(
            options=dropdown_dict, description='', disabled=tmp_disabled,
            value=group_idx, margin='0.1cm')
        self.group_selection_box = ipywidgets.HBox(
            children=[self.group_description, self.group_slider,
                      self.group_dropdown], visible=tmp_visible, align='center')
        # Link the values of group dropdown and slider
        self.link_group_dropdown_and_slider = link(
            (self.group_dropdown, 'value'), (self.group_slider, 'value'))
        # Create labels
        self.labels_toggles = [
            [ipywidgets.ToggleButton(description=k, value=True,
                                     visible=tmp_visible, disabled=tmp_disabled)
             for k in s_keys]
            for s_keys in landmark_options['labels_keys']]
        self.labels_text = ipywidgets.Latex(value='Labels', visible=tmp_visible)
        self.labels_box = ipywidgets.HBox(
            children=self.labels_toggles[group_idx])
        self.labels_and_text_box = ipywidgets.HBox(children=[self.labels_text,
                                                             self.labels_box],
                                                   align='center')
        self._set_labels_toggles_values(landmark_options['with_labels'])
        self.group_and_labels_and_text_box = ipywidgets.VBox(
            children=[self.group_selection_box, self.labels_and_text_box])
        super(LandmarkOptionsWidget, self).__init__(
            children=[self.landmarks_checkbox_and_msg_box,
                      self.group_and_labels_and_text_box])
        self.align = 'start'
        self.labels_box.padding = '0.3cm'

        # Assign output
        self.selected_values = landmark_options

        # Set style
        self.predefined_style(style)

        # Set functionality
        def render_landmarks_fun(name, value):
            # save render_landmarks value
            self.selected_values['render_landmarks'] = value
            # disable group drop down menu
            self.group_dropdown.disabled = not value
            self.group_slider.disabled = not value
            # set disability of all labels toggles
            for s_keys in self.labels_toggles:
                for k in s_keys:
                    k.disabled = not value
            # if all currently selected labels toggles are False, set them all
            # to True
            self._all_labels_false_1()
        self.render_landmarks_checkbox.on_trait_change(render_landmarks_fun,
                                                       'value')

        def group_fun(name, value):
            # save group value
            self.selected_values['group'] = \
                self.selected_values['group_keys'][value]
            # assign the correct children to the labels toggles
            self.labels_box.children = self.labels_toggles[value]
            # save with_labels value
            self._save_with_labels()
        self.group_dropdown.on_trait_change(group_fun, 'value')

        def labels_fun(name, value):
            # if all labels toggles are False, set render landmarks checkbox to
            # False
            self._all_labels_false_2()
            # save with_labels value
            self._save_with_labels()
        # assign labels_fun to all labels toggles (even hidden ones)
        self._add_function_to_labels_toggles(labels_fun)

        # Store functions
        self._render_landmarks_fun = render_landmarks_fun
        self._group_fun = group_fun
        self._labels_fun = labels_fun

        # Set render function
        self._update_function = None
        self.add_update_function(update_function)
        self._render_function = None
        self.add_render_function(render_function)

    def _parse_landmark_options_dict(self, landmark_options):
        if (len(landmark_options['group_keys']) == 1 and
                landmark_options['group_keys'][0] == ' '):
            landmark_options['has_landmarks'] = False
        if not landmark_options['has_landmarks']:
            landmark_options['render_landmarks'] = False
            landmark_options['group_keys'] = [' ']
            landmark_options['group'] = ' '
            landmark_options['labels_keys'] = [[' ']]
            landmark_options['with_labels'] = [' ']
        else:
            if (landmark_options['with_labels'] is not None and
                    len(landmark_options['with_labels']) == 0):
                landmark_options['with_labels'] = None
        return landmark_options

    def _no_landmarks_msg_visible(self, has_landmarks):
        return not has_landmarks

    def _options_visible(self, has_landmarks):
        return has_landmarks

    def _group_slider_visible(self, group_keys):
        return len(group_keys) > 1

    def _all_labels_false_1(self):
        r"""
        If all currently selected labels toggles are ``False``, set them all to
        ``True``.
        """
        # get all values of current labels toggles
        all_values = [ww.value for ww in self.labels_box.children]
        # if all of them are False
        if all(item is False for item in all_values):
            for ww in self.labels_box.children:
                # temporarily remove render function
                ww.on_trait_change(self._render_function, 'value', remove=True)
                # set value
                ww.value = True
                # re-add render function
                ww.on_trait_change(self._render_function, 'value')

    def _all_labels_false_2(self):
        r"""
        If all currently selected labels toggles are ``False``, set
        `render_landmarks_checkbox` to ``False``.
        """
        # get all values of current labels toggles
        all_values = [ww.value for ww in self.labels_box.children]
        # if all of them are False
        if all(item is False for item in all_values):
            # temporarily remove render function
            self.render_landmarks_checkbox.on_trait_change(
                self._render_function, 'value', remove=True)
            # set value
            self.render_landmarks_checkbox.value = False
            # re-add render function
            self.render_landmarks_checkbox.on_trait_change(
                self._render_function, 'value')

    def _save_with_labels(self):
        r"""
        Saves `with_labels` value to the `selected_values` dictionary.
        """
        self.selected_values['with_labels'] = []
        for ww in self.labels_box.children:
            if ww.value:
                self.selected_values['with_labels'].append(
                    str(ww.description))

    def _set_labels_toggles_values(self, with_labels):
        for w in self.labels_box.children:
            if w.description not in with_labels:
                w.value = False
            else:
                w.value = True

    def _add_function_to_labels_toggles(self, fun):
        r"""
        Adds a function callback to all labels toggles.
        """
        for s_group in self.labels_toggles:
            for w in s_group:
                w.on_trait_change(fun, 'value')

    def _remove_function_from_labels_toggles(self, fun):
        r"""
        Removes a function callback from all labels toggles.
        """
        for s_group in self.labels_toggles:
            for w in s_group:
                w.on_trait_change(fun, 'value', remove=True)

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight='', labels_buttons_style=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}

        labels_buttons_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'primary' Blue-based style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.render_landmarks_checkbox, font_family, font_size,
                    font_style, font_weight)
        format_font(self.group_dropdown, font_family, font_size, font_style,
                    font_weight)
        format_font(self.group_description, font_family, font_size, font_style,
                    font_weight)
        for s_group in self.labels_toggles:
            for w in s_group:
                format_font(w, font_family, font_size, font_style, font_weight)
                w.button_style = labels_buttons_style
        format_font(self.labels_text, font_family, font_size, font_style,
                    font_weight)

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style=None, border_visible=True,
                       border_color='black', border_style='solid',
                       border_width=1, border_radius=0, padding='0.2cm',
                       margin='0.3cm', font_family='', font_size=None,
                       font_style='', font_weight='', labels_buttons_style='')
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       labels_buttons_style='primary')
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function = render_function
        if self._render_function is not None:
            self.render_landmarks_checkbox.on_trait_change(
                self._render_function, 'value')
            self.group_dropdown.on_trait_change(self._render_function, 'value')
            self._add_function_to_labels_toggles(self._render_function)

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        self.render_landmarks_checkbox.on_trait_change(self._render_function,
                                                       'value', remove=True)
        self.group_dropdown.on_trait_change(self._render_function, 'value',
                                            remove=True)
        self._remove_function_from_labels_toggles(self._render_function)
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)

    def add_update_function(self, update_function):
        r"""
        Method that adds an `update_function()` to the widget. The signature of
        the given function is also stored in `self._update_function`.

        Parameters
        ----------
        update_function : `function` or ``None``, optional
            The update function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._update_function = update_function
        if self._update_function is not None:
            self.render_landmarks_checkbox.on_trait_change(
                self._update_function, 'value')
            self.group_dropdown.on_trait_change(self._update_function, 'value')
            self._add_function_to_labels_toggles(self._update_function)

    def remove_update_function(self):
        r"""
        Method that removes the current `self._update_function()` from the
        widget and sets ``self._update_function = None``.
        """
        self.render_landmarks_checkbox.on_trait_change(self._update_function,
                                                       'value', remove=True)
        self.group_dropdown.on_trait_change(self._update_function, 'value',
                                            remove=True)
        self._remove_function_from_labels_toggles(self._update_function)
        self._update_function = None

    def replace_update_function(self, update_function):
        r"""
        Method that replaces the current `self._update_function()` of the widget
        with the given `update_function()`.

        Parameters
        ----------
        update_function : `function` or ``None``, optional
            The update function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_update_function()

        # add new function
        self.add_update_function(update_function)

    def _compare_groups_and_labels(self, groups, labels):
        r"""
        Function that compares the provided landmarks groups and labels with
        `self.selected_values['group_keys']` and
        `self.selected_values['labels_keys']`.

        Parameters
        ----------
        groups : `list` of `str`
            The new `list` of landmark groups.
        labels : `list` of `list` of `str`
            The new `list` of `list`s of each landmark group's labels.

        Returns
        -------
        _compare_groups_and_labels : `bool`
            ``True`` if the groups and labels are identical with the ones stored
            in `self.selected_values['group_keys']` and
            `self.selected_values['labels_keys']`.
        """
        # function that compares two lists without taking into account the order
        def comp_lists(l1, l2):
            len_match = len(l1) == len(l2)
            return len_match and np.all([g1 == g2 for g1, g2 in zip(l1, l2)])

        # comparison of the given groups
        groups_same = comp_lists(groups, self.selected_values['group_keys'])

        # if groups are the same, then compare the labels
        if groups_same:
            len_match = len(labels) == len(self.selected_values['labels_keys'])
            tmp = [comp_lists(g1, g2)
                   for g1, g2 in zip(labels,
                                     self.selected_values['labels_keys'])]
            return len_match and np.all(tmp)
        else:
            return False

    def set_widget_state(self, landmark_options, allow_callback=True):
        r"""
        Method that updates the state of the widget with a new set of values.

        Parameters
        ----------
        landmark_options : `dict`
            The dictionary with the new options to be used. For example
            ::

                landmark_options = {'has_landmarks': True,
                                    'render_landmarks': True,
                                    'group_keys': ['PTS', 'ibug_face_68'],
                                    'labels_keys': [['all'], ['jaw', 'eye']],
                                    'group': 'PTS',
                                    'with_labels': ['all']}

        allow_callback : `bool`, optional
            If ``True``, it allows triggering of any callback functions.
        """
        # temporarily remove render callback
        render_function = self._render_function
        self.remove_render_function()
        update_function = self._update_function
        self.remove_update_function()

        # temporarily remove the rest of the callbacks
        self.render_landmarks_checkbox.on_trait_change(
            self._render_landmarks_fun, 'value', remove=True)
        self.group_dropdown.on_trait_change(self._group_fun, 'value',
                                            remove=True)
        self._remove_function_from_labels_toggles(self._labels_fun)

        # Check given options
        landmark_options = self._parse_landmark_options_dict(landmark_options)

        # Temporarily store visible and disabled values
        tmp_visible = self._options_visible(landmark_options['has_landmarks'])
        tmp_disabled = not landmark_options['render_landmarks']
        tmp_slider_visible = self._group_slider_visible(
            landmark_options['group_keys'])

        # Update widgets
        self.no_landmarks_msg.visible = self._no_landmarks_msg_visible(
            landmark_options['has_landmarks'])
        self.render_landmarks_checkbox.value = \
            landmark_options['render_landmarks']
        self.render_landmarks_checkbox.visible = tmp_visible
        self.labels_text.visible = tmp_visible

        # Check if group_keys and labels_keys are the same with the existing
        # ones
        if not self._compare_groups_and_labels(landmark_options['group_keys'],
                                               landmark_options['labels_keys']):
            if landmark_options['group'] is None:
                landmark_options['group'] = landmark_options['group_keys'][0]
            group_idx = landmark_options['group_keys'].index(
                landmark_options['group'])

            dropdown_dict = OrderedDict()
            for gn, gk in enumerate(landmark_options['group_keys']):
                dropdown_dict[gk] = gn

            self.group_selection_box.visible = tmp_visible
            self.group_dropdown.options = dropdown_dict
            self.group_dropdown.disabled = tmp_disabled
            self.group_slider.max = len(landmark_options['group_keys']) - 1
            self.group_slider.disabled = tmp_disabled
            self.group_slider.visible = tmp_slider_visible
            self.group_dropdown.value = group_idx

            self.labels_toggles = [
                [ipywidgets.ToggleButton(description=k, disabled=tmp_disabled,
                                         visible=tmp_visible, value=True)
                 for k in s_keys]
                for s_keys in landmark_options['labels_keys']]
            self.labels_box.children = self.labels_toggles[group_idx]
            if landmark_options['with_labels'] is None:
                landmark_options['with_labels'] = \
                    landmark_options['labels_keys'][group_idx]
            self._set_labels_toggles_values(landmark_options['with_labels'])
        else:
            self.group_selection_box.visible = tmp_visible
            self.group_slider.disabled = tmp_disabled
            self.group_dropdown.disabled = tmp_disabled

            if landmark_options['group'] is None:
                landmark_options['group'] = self.selected_values['group']
            group_idx = landmark_options['group_keys'].index(
                landmark_options['group'])
            self.group_dropdown.value = group_idx

            if landmark_options['with_labels'] is None:
                landmark_options['with_labels'] = \
                    self.selected_values['with_labels']
            self._set_labels_toggles_values(landmark_options['with_labels'])

            for w in self.labels_box.children:
                w.disabled = tmp_disabled
                w.visible = tmp_visible

        # Re-assign the rest of the callbacks
        self.render_landmarks_checkbox.on_trait_change(
            self._render_landmarks_fun, 'value')
        self.group_dropdown.on_trait_change(self._group_fun, 'value')
        self._add_function_to_labels_toggles(self._labels_fun)

        # Assign new options dict to selected_values
        self.selected_values = landmark_options

        # Re-assign render callback
        self.add_update_function(update_function)
        self.add_render_function(render_function)

        # trigger render function if allowed
        if allow_callback:
            self._update_function('', True)
            self._render_function('', True)


class TextPrintWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for printing text. Specifically, it consists of a `list`
    of `IPython.html.widgets.Latex` objects, i.e. one per text line.

    Note that:

    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.

    Parameters
    ----------
    n_lines : `int`
        The number of lines of the text to be printed.
    text_per_line : `list` of length `n_lines`
        The text to be printed per line.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create an text widget and then update its state. Firstly, we need
    to import it:

        >>> from menpowidgets.options import TextPrintWidget
        >>> from IPython.display import display

    Create the widget with some initial options and display it:

        >>> n_lines = 3
        >>> text_per_line = ['> The', '> Menpo', '> Team']
        >>> wid = TextPrintWidget(n_lines, text_per_line, style='success')
        >>> display(wid)

    The style of the widget can be changed as:

        >>> wid.predefined_style('danger')

    Update the widget state as:

        >>> wid.set_widget_state(5, ['M', 'E', 'N', 'P', 'O'])
    """
    def __init__(self, n_lines, text_per_line, style='minimal'):
        self.latex_texts = [ipywidgets.Latex(value=text_per_line[i])
                            for i in range(n_lines)]
        super(TextPrintWidget, self).__init__(children=self.latex_texts)
        self.align = 'start'

        # Assign options
        self.n_lines = n_lines
        self.text_per_line = text_per_line

        # Set style
        self.predefined_style(style)

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}

        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        for i in range(self.n_lines):
            format_font(self.latex_texts[i], font_family, font_size,
                        font_style, font_weight)

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style=None, border_visible=True,
                       border_color='black', border_style='solid',
                       border_width=1, border_radius=0, padding='0.1cm',
                       margin='0.3cm', font_family='', font_size=None,
                       font_style='', font_weight='')
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.1cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='')
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def set_widget_state(self, n_lines, text_per_line):
        r"""
        Method that updates the state of the widget with a new set of values.

        Parameters
        ----------
        n_lines : `int`
            The number of lines of the text to be printed.
        text_per_line : `list` of length `n_lines`
            The text to be printed per line.
        """
        # Check if n_lines has changed
        if n_lines != self.n_lines:
            self.latex_texts = [ipywidgets.Latex(value=text_per_line[i])
                                for i in range(n_lines)]
            self.children = self.latex_texts
        else:
            for i in range(n_lines):
                self.latex_texts[i].value = text_per_line[i]
        self.n_lines = n_lines
        self.text_per_line = text_per_line


class AnimationOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for animating through a list of objects. The widget
    consists of the following parts from `IPython.html.widgets` and
    `menpowidgets.tools`:

    == ================== ===================== ====================
    No Object             Variable (`self.`)    Description
    == ================== ===================== ====================
    1  ToggleButton       `play_stop_toggle`    The play/stop button
    2  ToggleButton       `play_options_toggle` Button that toggles

                                                the options menu
    3  Checkbox           `loop_checkbox`       Repeat mode
    4  FloatText          `interval_text`       Interval (secs)
    5  VBox               `loop_interval_box`   Contains 3, 4
    6  VBox               `play_options_box`    Contains 2, 5
    7  HBox               `animation_box`       Contains 1, 6
    8  IndexButtonsWidget `index_wid`           The index selector

       IndexSliderWidget                        widget
    == ================== ===================== ====================

    Note that:

    * The selected values are stored in the ``self.selected_values`` `dict`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` and ``replace_update_function()`` methods.

    Parameters
    ----------
    index : `dict`
        The dictionary with the initial options. For example
        ::

            index = {'min': 0,
                     'max': 100,
                     'step': 1,
                     'index': 10}

    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    update_function : `function` or ``None``, optional
        The update function that is executed when the index value changes.
        If ``None``, then nothing is assigned.
    index_style : {``'buttons'``, ``'slider'``}, optional
        If ``'buttons'``, then `IndexButtonsWidget()` class is called. If
        ``'slider'``, then 'IndexSliderWidget()' class is called.
    interval : `float`, optional
        The interval between the animation progress.
    description : `str`, optional
        The title of the widget.
    minus_description : `str`, optional
        The title of the button that decreases the index.
    plus_description : `str`, optional
        The title of the button that increases the index.
    loop_enabled : `bool`, optional
        If ``True``, then after reach the minimum (maximum) index values, the
        counting will continue from the end (beginning). If ``False``, the
        counting will stop at the minimum (maximum) value.
    text_editable : `bool`, optional
        Flag that determines whether the index text will be editable.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create an animation widget and then update its state. Firstly, we need
    to import it:

        >>> from menpowidgets.options import AnimationOptionsWidget
        >>> from IPython.display import display

    Now let's define a render function that will get called on every widget
    change and will dynamically print the selected index:

        >>> from menpo.visualize import print_dynamic
        >>> def render_function(name, value):
        >>>     s = "Selected index: {}".format(wid.selected_values['index'])
        >>>     print_dynamic(s)

    Create the widget with some initial options and display it:

        >>> index = {'min': 0, 'max': 100, 'step': 1, 'index': 10}
        >>> wid = AnimationOptionsWidget(index, index_style='buttons',
        >>>                              render_function=render_function,
        >>>                              style='info')
        >>> display(wid)

    By pressing the buttons (or simply pressing the Play button), the printed
    message gets updated. Finally, let's change the widget status with a new
    dictionary of options:

        >>> new_options = {'min': 0, 'max': 20, 'step': 2, 'index': 16}
        >>> wid.set_widget_state(new_options, allow_callback=False)
    """
    def __init__(self, index, render_function=None, update_function=None,
                 index_style='buttons', interval=0.5, description='Index: ',
                 minus_description='-', plus_description='+', loop_enabled=True,
                 text_editable=True, style='minimal'):
        from time import sleep
        from IPython import get_ipython

        # Get the kernel to use it later in order to make sure that the widgets'
        # traits changes are passed during a while-loop
        kernel = get_ipython().kernel

        # Create index widget
        if index_style == 'slider':
            self.index_wid = IndexSliderWidget(index, description=description)
        elif index_style == 'buttons':
            self.index_wid = IndexButtonsWidget(
                index, description=description,
                minus_description=minus_description,
                plus_description=plus_description, loop_enabled=loop_enabled,
                text_editable=text_editable)
        else:
            raise ValueError('index_style should be either slider or buttons')
        self.index_wid.style(box_style=None, border_visible=False,
                             padding=0, margin='0.15cm')

        # Create other widgets
        self.play_stop_toggle = ipywidgets.ToggleButton(description='Play >',
                                                        value=False)
        self._toggle_play_style = 'success'
        self._toggle_stop_style = 'danger'
        if style == 'minimal':
            self._toggle_play_style = ''
            self._toggle_stop_style = ''
        self.play_options_toggle = ipywidgets.ToggleButton(
            description='Options', value=False,
            button_style=self._toggle_play_style)
        self.loop_checkbox = ipywidgets.Checkbox(description='Loop',
                                                 value=loop_enabled)
        self.interval_text = ipywidgets.FloatText(description='Interval (sec)',
                                                  value=interval)
        self.loop_interval_box = ipywidgets.VBox(
            children=[self.interval_text, self.loop_checkbox], visible=False,
            margin='0.1cm', padding='0.1cm', border_color='black',
            border_style='solid', border_width=1)
        self.play_options_box = ipywidgets.VBox(
            children=[self.play_options_toggle, self.loop_interval_box])
        self.animation_box = ipywidgets.HBox(
            children=[self.play_stop_toggle, self.play_options_box],
            margin='0.15cm', padding=0)
        super(AnimationOptionsWidget, self).__init__(
            children=[self.index_wid, self.animation_box])
        self.align = 'start'
        self.orientation = 'horizontal'

        # Assign output
        self.selected_values = index
        self.index_style = index_style

        # Set style
        self.predefined_style(style)

        # Set functionality
        def play_stop_pressed(name, value):
            if value:
                # Animation was not playing, so Play was pressed.
                # Change the button style
                self.play_stop_toggle.button_style = self._toggle_stop_style
                # Change the description to Stop
                self.play_stop_toggle.description = 'Stop -'
                # Make sure that play options are off
                self.play_options_toggle.value = False
            else:
                # Animation was playing, so Stop was pressed.
                # Change the button style
                self.play_stop_toggle.button_style = self._toggle_play_style
                # Change the description to Play
                self.play_stop_toggle.description = 'Play >'
            self.play_options_toggle.disabled = value
        self.play_stop_toggle.on_trait_change(play_stop_pressed, 'value')

        def play_options_visibility(name, value):
            self.loop_interval_box.visible = value
        self.play_options_toggle.on_trait_change(play_options_visibility,
                                                 'value')

        def animate(name, value):
            if self.loop_checkbox.value:
                # loop is enabled
                i = self.selected_values['index']
                if i < self.selected_values['max']:
                    i += self.selected_values['step']
                else:
                    i = self.selected_values['min']

                while (i <= self.selected_values['max'] and
                       self.play_stop_toggle.value):
                    # update index value
                    if index_style == 'slider':
                        self.index_wid.slider.value = i
                    else:
                        self.index_wid.index_text.value = i

                    # Run IPython iteration.
                    # This is the code that makes this operation non-blocking.
                    # This allows widget messages and callbacks to be processed.
                    kernel.do_one_iteration()

                    # update counter
                    if i < self.selected_values['max']:
                        i += self.selected_values['step']
                    else:
                        i = self.selected_values['min']

                    # wait
                    sleep(self.interval_text.value)
            else:
                # loop is disabled
                i = self.selected_values['index']
                i += self.selected_values['step']
                while (i <= self.selected_values['max'] and
                       self.play_stop_toggle.value):
                    # update index value
                    if index_style == 'slider':
                        self.index_wid.slider.value = i
                    else:
                        self.index_wid.index_text.value = i

                    # Run IPython iteration.
                    # This is the code that makes this operation non-blocking.
                    # This allows widget messages and callbacks to be processed.
                    kernel.do_one_iteration()

                    # update counter
                    i += self.selected_values['step']

                    # wait
                    sleep(self.interval_text.value)
                if i > self.selected_values['max']:
                    self.play_stop_toggle.value = False
        self.play_stop_toggle.on_trait_change(animate, 'value')

        # Set render and update functions
        self._update_function = None
        self.add_update_function(update_function)
        self._render_function = None
        self.add_render_function(render_function)

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.play_stop_toggle, font_family, font_size, font_style,
                    font_weight)
        format_font(self.play_options_toggle, font_family, font_size,
                    font_style, font_weight)
        format_font(self.loop_checkbox, font_family, font_size, font_style,
                    font_weight)
        format_font(self.interval_text, font_family, font_size, font_style,
                    font_weight)
        if self.index_style == 'buttons':
            self.index_wid.style(
                box_style=None, border_visible=False, padding=0,
                margin='0.15cm', font_family=font_family, font_size=font_size,
                font_style=font_style, font_weight=font_weight)
        else:
            self.index_wid.style(
                box_style=None, border_visible=False, padding=0,
                margin='0.15cm', font_family=font_family, font_size=font_size,
                font_style=font_style, font_weight=font_weight)

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style='', border_visible=False)
            self.play_stop_toggle.button_style = ''
            self.play_stop_toggle.font_weight = 'normal'
            self.play_options_toggle.button_style = ''
            format_box(self.loop_interval_box, '', False, 'black', 'solid', 1,
                       10, '0.1cm', '0.1cm')
            if self.index_style == 'buttons':
                self.index_wid.button_plus.button_style = ''
                self.index_wid.button_plus.font_weight = 'normal'
                self.index_wid.button_minus.button_style = ''
                self.index_wid.button_minus.font_weight = 'normal'
                self.index_wid.index_text.background_color = None
            elif self.index_style == 'slider':
                self.index_wid.slider.slider_color = None
                self.index_wid.slider.background_color = None
            self._toggle_play_style = ''
            self._toggle_stop_style = ''
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=False)
            self.play_stop_toggle.button_style = 'success'
            self.play_stop_toggle.font_weight = 'bold'
            self.play_options_toggle.button_style = 'info'
            format_box(self.loop_interval_box, 'info', True,
                       map_styles_to_hex_colours('info'), 'solid', 1, 10,
                       '0.1cm', '0.1cm')
            if self.index_style == 'buttons':
                self.index_wid.button_plus.button_style = 'primary'
                self.index_wid.button_plus.font_weight = 'bold'
                self.index_wid.button_minus.button_style = 'primary'
                self.index_wid.button_minus.font_weight = 'bold'
                self.index_wid.index_text.background_color = \
                    map_styles_to_hex_colours(style, True)
            elif self.index_style == 'slider':
                self.index_wid.slider.slider_color = \
                    map_styles_to_hex_colours(style)
                self.index_wid.slider.background_color = \
                    map_styles_to_hex_colours(style)
            self._toggle_play_style = 'success'
            self._toggle_stop_style = 'danger'
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function = render_function
        if self._render_function is not None:
            self.index_wid.add_render_function(self._render_function)

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        self.index_wid.remove_render_function()
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)

    def add_update_function(self, update_function):
        r"""
        Method that adds an `update_function()` to the widget. The signature of
        the given function is also stored in `self._update_function`.

        Parameters
        ----------
        update_function : `function` or ``None``, optional
            The update function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._update_function = update_function
        if self._update_function is not None:
            self.index_wid.add_update_function(self._update_function)

    def remove_update_function(self):
        r"""
        Method that removes the current `self._update_function()` from the
        widget and sets ``self._update_function = None``.
        """
        self.index_wid.remove_update_function()
        self._update_function = None

    def replace_update_function(self, update_function):
        r"""
        Method that replaces the current `self._update_function()` of the widget
        with the given `update_function()`.

        Parameters
        ----------
        update_function : `function` or ``None``, optional
            The update function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_update_function()

        # add new function
        self.add_update_function(update_function)

    def set_widget_state(self, index, allow_callback=True):
        r"""
        Method that updates the state of the widget with a new set of values.

        Parameters
        ----------
        index : `dict`
            The dictionary with the new options to be used. For example
            ::

                index = {'min': 0,
                         'max': 100,
                         'step': 1,
                         'index': 10}

        allow_callback : `bool`, optional
            If ``True``, it allows triggering of any callback functions.
        """
        if self.play_stop_toggle.value:
            self.play_stop_toggle.value = False
        if self.index_style == 'slider':
            self.index_wid.set_widget_state(index,
                                            allow_callback=allow_callback)
        else:
            self.index_wid.set_widget_state(
                index, loop_enabled=self.index_wid.loop_enabled,
                text_editable=self.index_wid.text_editable,
                allow_callback=allow_callback)
        self.selected_values = index


class RendererOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for selecting rendering options. The widget consists of the
    following parts from `IPython.html.widgets` and
    `menpowidgets.tools`:

    == ====================== =========================== ===================
    No Object                 Variable (`self.`)          Description
    == ====================== =========================== ===================
    1  Dropdown               `object_selection_dropdown` The object selector
    2  LineOptionsWidget      `options_widgets`           `list` with the

       MarkerOptionsWidget                                various rendering

       ImageOptionsWidget                                 sub-options widgets

       NumberingOptionsWidget

       FigureOptionsWidget

       LegendOptionsWidget

       GridOptionsWidget
    3  Tab                    `suboptions_tab`            Contains all 2
    == ====================== =========================== ===================

    Note that:

    * The selected values are stored in the ``self.selected_values`` `dict`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` methods.

    Parameters
    ----------
    renderer_options : `list` of `dict`
        The initial rendering options per object. The `list` must have length
        `n_objects` and contain a `dict` of rendering options per object.
        For example, in case we had two objects to render
        ::

            lines_options = {'render_lines': True,
                             'line_width': 1,
                             'line_colour': ['b', 'r'],
                             'line_style': '-'}
            markers_options = {'render_markers': True,
                               'marker_size': 20,
                               'marker_face_colour': ['w', 'w'],
                               'marker_edge_colour': ['b', 'r'],
                               'marker_style': 'o',
                               'marker_edge_width': 1}
            numbering_options = {'render_numbering': True,
                                 'numbers_font_name': 'serif',
                                 'numbers_font_size': 10,
                                 'numbers_font_style': 'normal',
                                 'numbers_font_weight': 'normal',
                                 'numbers_font_colour': ['k'],
                                 'numbers_horizontal_align': 'center',
                                 'numbers_vertical_align': 'bottom'}
            legend_options = {'render_legend': True,
                              'legend_title': '',
                              'legend_font_name': 'serif',
                              'legend_font_style': 'normal',
                              'legend_font_size': 10,
                              'legend_font_weight': 'normal',
                              'legend_marker_scale': 1.,
                              'legend_location': 2,
                              'legend_bbox_to_anchor': (1.05, 1.),
                              'legend_border_axes_pad': 1.,
                              'legend_n_columns': 1,
                              'legend_horizontal_spacing': 1.,
                              'legend_vertical_spacing': 1.,
                              'legend_border': True,
                              'legend_border_padding': 0.5,
                              'legend_shadow': False,
                              'legend_rounded_corners': True}
            figure_options = {'x_scale': 1.,
                              'y_scale': 1.,
                              'render_axes': True,
                              'axes_font_name': 'serif',
                              'axes_font_size': 10,
                              'axes_font_style': 'normal',
                              'axes_font_weight': 'normal',
                              'axes_x_limits': None,
                              'axes_y_limits': None}
            grid_options = {'render_grid': True,
                            'grid_line_style': '--',
                            'grid_line_width': 0.5}
            image_options = {'alpha': 1.,
                             'interpolation': 'bilinear',
                             'cmap_name': 'gray'}
            rendering_dict = {'lines': lines_options,
                              'markers': markers_options,
                              'numbering': numbering_options,
                              'legend': legend_options,
                              'figure': figure_options,
                              'grid': grid_options,
                              'image': image_options}
            renderer_options = [rendering_dict, rendering_dict]

    options_tabs : `list` of `str`
        `List` that defines the ordering of the options tabs. Possible values
        are

            ============= ===============================
            Value         Returned class
            ============= ===============================
            'lines'       `LineOptionsWidget`
            'markers'     `MarkerOptionsWidget`
            'numbering'   `NumberingOptionsWidget`
            'figure_one'  `FigureOptionsOneScaleWidget`
            'figure_two'  `FigureOptionsTwoScalesWidget`
            'legend'      `LegendOptionsWidget`
            'grid'        `GridOptionsWidget`
            'image'       `ImageOptionsWidget`
            ============= ===============================

    objects_names : `list` of `str` or ``None``, optional
        A `list` with the names of the objects that will be used in the
        selection dropdown menu. If ``None``, then the names will have the
        format ``%d``.
    labels_per_object : `list` of `list` or ``None``, optional
        A `list` that contains a `list` of labels for each object. Those
        `labels` are employed by the `ColourSelectionWidget`. An example for
        which this option is useful is in the case we wish to create rendering
        options for multiple :map:`LandmarkGroup` objects and each one of them
        has a different set of `labels`. If ``None``, then `labels_per_object`
        is a `list` of length `n_objects` with ``None``.
    selected_object : `int`, optional
        The object for which to show the rendering options in the beginning,
        when the widget is created.
    object_selection_dropdown_visible : `bool`, optional
        Controls the visibility of the object selection dropdown
        (`self.object_selection_dropdown`).
    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    tabs_style : See Below, optional
        Sets a predefined style at the tabs of the widget. Possible options
        are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create a rendering options widget and then update its state. Firstly,
    we need to import it:

        >>> from menpowidgets.options import RendererOptionsWidget
        >>> from IPython.display import display

    Let's set some initial options:

        >>> options_tabs = ['markers', 'lines', 'grid']
        >>> objects_names = ['james', 'patrick']
        >>> labels_per_object = [['jaw', 'eyes'], None]
        >>> selected_object = 1
        >>> object_selection_dropdown_visible = True

    Now let's define a render function that will get called on every widget
    change and will dynamically print the selected marker face colour for both
    objects:

        >>> from menpo.visualize import print_dynamic
        >>> def render_function(name, value):
        >>>     s = "{}: {}, {}: {}".format(
        >>>         wid.objects_names[0],
        >>>         wid.selected_values[0]['markers']['marker_face_colour'],
        >>>         wid.objects_names[1],
        >>>         wid.selected_values[1]['markers']['marker_face_colour'])
        >>>     print_dynamic(s)

    Create the widget with some initial options and display it:

        >>> # 1st dictionary
        >>> markers_options = {'render_markers': True, 'marker_size': 20,
        >>>                    'marker_face_colour': ['w', 'w'],
        >>>                    'marker_edge_colour': ['b', 'r'],
        >>>                    'marker_style': 'o', 'marker_edge_width': 1}
        >>> lines_options = {'render_lines': True, 'line_width': 1,
        >>>                  'line_colour': ['b', 'r'], 'line_style': '-'}
        >>> grid_options = {'render_grid': True, 'grid_line_style': '--',
        >>>                 'grid_line_width': 0.5}
        >>> rendering_dict_1 = {'lines': lines_options, 'grid': grid_options,
        >>>                     'markers': markers_options}
        >>>
        >>> # 2nd dictionary
        >>> markers_options = {'render_markers': True, 'marker_size': 200,
        >>>                    'marker_face_colour': [[0.1, 0.2, 0.3]],
        >>>                    'marker_edge_colour': ['m'], 'marker_style': 'x',
        >>>                    'marker_edge_width': 1}
        >>> lines_options = {'render_lines': True, 'line_width': 100,
        >>>                  'line_colour': [[0.1, 0.2, 0.3]], 'line_style': '-'}
        >>> grid_options = {'render_grid': False, 'grid_line_style': '--',
        >>>                 'grid_line_width': 0.5}
        >>> rendering_dict_2 = {'lines': lines_options, 'grid': grid_options,
        >>>                     'markers': markers_options}
        >>>
        >>> # Final list
        >>> rendering_options = [rendering_dict_1, rendering_dict_2]
        >>>
        >>> # Create and display widget
        >>> wid = AnimationOptionsWidget(index, index_style='buttons',
        >>>                              render_function=render_function,
        >>>                              style='info')
        >>> display(wid)

    By playing around, the printed message gets updated. The style of the widget
    can be changed as:

        >>> wid.predefined_style('minimal', 'info')

    Finally, let's change
    the widget status with a new dictionary of options:

        >>> # 1st dictionary
        >>> markers_options = {'render_markers': False, 'marker_size': 20,
        >>>                    'marker_face_colour': ['k'],
        >>>                    'marker_edge_colour': ['c'],
        >>>                    'marker_style': 'o', 'marker_edge_width': 1}
        >>> lines_options = {'render_lines': False, 'line_width': 1,
        >>>                  'line_colour': ['r'], 'line_style': '-'}
        >>> grid_options = {'render_grid': True, 'grid_line_style': '--',
        >>>                 'grid_line_width': 0.5}
        >>> rendering_dict_1 = {'lines': lines_options, 'grid': grid_options,
        >>>                     'markers': markers_options}
        >>>
        >>> # 2nd dictionary
        >>> markers_options = {'render_markers': True, 'marker_size': 200,
        >>>                    'marker_face_colour': [[0.123, 0.234, 0.345], 'r'],
        >>>                    'marker_edge_colour': ['m', 'm'],
        >>>                    'marker_style': 'x', 'marker_edge_width': 1}
        >>> lines_options = {'render_lines': True, 'line_width': 100,
        >>>                  'line_colour': [[0.1, 0.2, 0.3], 'b'], 'line_style': '-'}
        >>> grid_options = {'render_grid': False, 'grid_line_style': '--',
        >>>                 'grid_line_width': 0.5}
        >>> rendering_dict_2 = {'lines': lines_options, 'grid': grid_options,
        >>>                     'markers': markers_options}
        >>>
        >>> # Final list
        >>> new_options = [rendering_dict_1, rendering_dict_2]
        >>>
        >>> # Set new labels per object
        >>> labels_per_object = [['1'], ['jaw', 'eyes']]
        >>>
        >>> # Update widget state
        >>> wid.set_widget_state(new_options, labels_per_object,
        >>>                      allow_callback=True)
    """
    def __init__(self, renderer_options, options_tabs, objects_names=None,
                 labels_per_object=None, selected_object=0,
                 object_selection_dropdown_visible=True, render_function=None,
                 style='minimal', tabs_style='minimal'):
        # Make sure that renderer_options is a list even with one member
        if not isinstance(renderer_options, list):
            renderer_options = [renderer_options]

        # Get number of objects to be rendered
        self.n_objects = len(renderer_options)

        # Check labels_per_object
        if labels_per_object is None:
            labels_per_object = [None] * self.n_objects

        # Check objects_names
        if objects_names is None:
            objects_names = [str(k) for k in range(self.n_objects)]

        # Create widgets
        # object selection dropdown
        objects_dict = OrderedDict()
        for k, g in enumerate(objects_names):
            objects_dict[g] = k
        tmp_visible = self._selection_dropdown_visible(
            object_selection_dropdown_visible)
        self.object_selection_dropdown = ipywidgets.Dropdown(
            options=objects_dict, value=selected_object, description='Select',
            visible=tmp_visible, margin='0.1cm')
        # options widgets
        options_widgets = []
        tab_titles = []
        for o in options_tabs:
            # get the options to pass to the sub-options constructors
            if o == 'figure_one' or o == 'figure_two':
                tmp_options = renderer_options[selected_object]['figure']
            else:
                tmp_options = renderer_options[selected_object][o]
            # get the labels to pass in where required
            tmp_labels = labels_per_object[selected_object]
            # call sub-options classes
            if o == 'lines':
                options_widgets.append(LineOptionsWidget(
                    tmp_options, render_function=render_function,
                    render_checkbox_title='Render lines', labels=tmp_labels))
                tab_titles.append('Lines')
            elif o == 'markers':
                options_widgets.append(MarkerOptionsWidget(
                    tmp_options, render_function=render_function,
                    render_checkbox_title='Render markers', labels=tmp_labels))
                tab_titles.append('Markers')
            elif o == 'image':
                options_widgets.append(ImageOptionsWidget(
                    tmp_options, render_function=render_function))
                tab_titles.append('Image')
            elif o == 'numbering':
                options_widgets.append(NumberingOptionsWidget(
                    tmp_options, render_function=render_function,
                    render_checkbox_title='Render numbering'))
                tab_titles.append('Numbering')
            elif o == 'figure_one':
                options_widgets.append(FigureOptionsOneScaleWidget(
                    tmp_options, render_function=render_function,
                    figure_scale_visible=True, axes_visible=True))
                tab_titles.append('Figure/Axes')
            elif o == 'figure_two':
                options_widgets.append(FigureOptionsTwoScalesWidget(
                    tmp_options, render_function=render_function,
                    figure_scale_visible=True, axes_visible=True,
                    coupled_default=False))
                tab_titles.append('Figure/Axes')
            elif o == 'legend':
                options_widgets.append(LegendOptionsWidget(
                    tmp_options, render_function=render_function,
                    render_checkbox_title='Render legend'))
                tab_titles.append('Legend')
            elif o == 'grid':
                options_widgets.append(GridOptionsWidget(
                    tmp_options, render_function=render_function,
                    render_checkbox_title='Render grid'))
                tab_titles.append('Grid')
        self.options_widgets = options_widgets
        self.tab_titles = tab_titles
        self.suboptions_tab = ipywidgets.Tab(children=options_widgets)
        # set titles
        for (k, tl) in enumerate(self.tab_titles):
            self.suboptions_tab.set_title(k, tl)
        self.options_box = ipywidgets.VBox(
            children=[self.object_selection_dropdown, self.suboptions_tab],
            align='center', padding='0.2cm')
        super(RendererOptionsWidget, self).__init__(children=[self.options_box])
        self.align = 'start'

        # Assign output
        self.selected_values = renderer_options
        self.options_tabs = options_tabs
        self.objects_names = objects_names
        self.labels_per_object = labels_per_object
        self.object_selection_dropdown_visible = \
            object_selection_dropdown_visible

        # Set style
        self.predefined_style(style, tabs_style)

        # Set functionality
        def update_widgets(name, value):
            for i, tab in enumerate(self.options_tabs):
                # get the options to pass to the sub-options update functions
                if tab == 'figure_one' or tab == 'figure_two':
                    tmp_options = self.selected_values[value]['figure']
                else:
                    tmp_options = self.selected_values[value][tab]
                # call sub-options classes
                if tab == 'lines' or tab == 'markers':
                    self.options_widgets[i].set_widget_state(
                        tmp_options, labels=self.labels_per_object[value],
                        allow_callback=False)
                else:
                    self.options_widgets[i].set_widget_state(
                        tmp_options, allow_callback=False)
        self.object_selection_dropdown.on_trait_change(update_widgets, 'value')

        # Set render function
        self._render_function = render_function

    def _selection_dropdown_visible(self, object_selection_dropdown_visible):
        return object_selection_dropdown_visible and self.n_objects > 1

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0,
              padding='0.2cm', margin=0, tabs_box_style=None,
              tabs_border_visible=True, tabs_border_color='black',
              tabs_border_style='solid', tabs_border_width=1,
              tabs_border_radius=1, tabs_padding=0, tabs_margin=0,
              font_family='', font_size=None, font_style='', font_weight=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        tabs_box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        tabs_border_visible : `bool`, optional
            Defines whether to draw the border line around the tab widgets.
        tabs_border_color : `str`, optional
            The color of the border around the tab widgets.
        tabs_border_style : `str`, optional
            The line style of the border around the tab widgets.
        tabs_border_width : `float`, optional
            The line width of the border around the tab widgets.
        tabs_border_radius : `float`, optional
            The radius of the corners of the box of the tab widgets.
        tabs_padding : `float`, optional
            The padding around the tab widgets.
        tabs_margin : `float`, optional
            The margin around the tab widgets.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        for wid in self.options_widgets:
            wid.style(box_style=tabs_box_style,
                      border_visible=tabs_border_visible,
                      border_color=tabs_border_color,
                      border_style=tabs_border_style,
                      border_width=tabs_border_width,
                      border_radius=tabs_border_radius, padding=tabs_padding,
                      margin=tabs_margin, font_family=font_family,
                      font_size=font_size, font_style=font_style,
                      font_weight=font_weight)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.object_selection_dropdown, font_family, font_size,
                    font_style, font_weight)

    def predefined_style(self, style, tabs_style='minimal'):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================

        tabs_style : `str` (see below), optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if tabs_style == 'minimal' or tabs_style=='':
            tabs_style = ''
            tabs_border_visible = False
            tabs_border_color = 'black'
            tabs_border_radius = 0
            tabs_padding = 0
        else:
            tabs_style = tabs_style
            tabs_border_visible = True
            tabs_border_color = map_styles_to_hex_colours(tabs_style)
            tabs_border_radius = 10
            tabs_padding = '0.3cm'

        if style == 'minimal':
            self.style(box_style='', border_visible=True, border_color='black',
                       border_style='solid', border_width=1, border_radius=0,
                       padding='0.2cm', margin='0.5cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       tabs_box_style=tabs_style,
                       tabs_border_visible=tabs_border_visible,
                       tabs_border_color=tabs_border_color,
                       tabs_border_style='solid', tabs_border_width=1,
                       tabs_border_radius=tabs_border_radius,
                       tabs_padding=tabs_padding, tabs_margin='0.1cm')
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.5cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       tabs_box_style=tabs_style,
                       tabs_border_visible=tabs_border_visible,
                       tabs_border_color=tabs_border_color,
                       tabs_border_style='solid', tabs_border_width=1,
                       tabs_border_radius=tabs_border_radius,
                       tabs_padding=tabs_padding, tabs_margin='0.1cm')
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function = render_function
        if self._render_function is not None:
            for wid in self.options_widgets:
                wid.add_render_function(self._render_function)

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        for wid in self.options_widgets:
            wid.remove_render_function()
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)

    def set_widget_state(self, renderer_options, labels_per_object,
                         selected_object=None,
                         object_selection_dropdown_visible=None,
                         allow_callback=True):
        r"""
        Method that updates the state of the widget with a new set of values.
        Note that the number of objects should not change.

        Parameters
        ----------
        renderer_options : `list` of `dict`
            The selected rendering options per object. The `list` must have
            length `n_objects` and contain a `dict` of rendering options per
            object. For example, in case we had two objects to render
            ::

                lines_options = {'render_lines': True,
                                 'line_width': 1,
                                 'line_colour': ['b', 'r'],
                                 'line_style': '-'}
                markers_options = {'render_markers': True,
                                   'marker_size': 20,
                                   'marker_face_colour': ['w', 'w'],
                                   'marker_edge_colour': ['b', 'r'],
                                   'marker_style': 'o',
                                   'marker_edge_width': 1}
                numbering_options = {'render_numbering': True,
                                     'numbers_font_name': 'serif',
                                     'numbers_font_size': 10,
                                     'numbers_font_style': 'normal',
                                     'numbers_font_weight': 'normal',
                                     'numbers_font_colour': ['k'],
                                     'numbers_horizontal_align': 'center',
                                     'numbers_vertical_align': 'bottom'}
                legend_options = {'render_legend': True,
                                  'legend_title': '',
                                  'legend_font_name': 'serif',
                                  'legend_font_style': 'normal',
                                  'legend_font_size': 10,
                                  'legend_font_weight': 'normal',
                                  'legend_marker_scale': 1.,
                                  'legend_location': 2,
                                  'legend_bbox_to_anchor': (1.05, 1.),
                                  'legend_border_axes_pad': 1.,
                                  'legend_n_columns': 1,
                                  'legend_horizontal_spacing': 1.,
                                  'legend_vertical_spacing': 1.,
                                  'legend_border': True,
                                  'legend_border_padding': 0.5,
                                  'legend_shadow': False,
                                  'legend_rounded_corners': True}
                figure_options = {'x_scale': 1.,
                                  'y_scale': 1.,
                                  'render_axes': True,
                                  'axes_font_name': 'serif',
                                  'axes_font_size': 10,
                                  'axes_font_style': 'normal',
                                  'axes_font_weight': 'normal',
                                  'axes_x_limits': None,
                                  'axes_y_limits': None}
                grid_options = {'render_grid': True,
                                'grid_line_style': '--',
                                'grid_line_width': 0.5}
                image_options = {'alpha': 1.,
                                 'interpolation': 'bilinear',
                                 'cmap_name': 'gray'}
                rendering_dict = {'lines': lines_options,
                                  'markers': markers_options,
                                  'numbering': numbering_options,
                                  'legend': legend_options,
                                  'figure': figure_options,
                                  'grid': grid_options
                                  'image': image_options}
                renderer_options = [rendering_dict, rendering_dict]

        labels_per_object : `list` of `list` or ``None``, optional
            A `list` that contains a `list` of labels for each object. Those
            `labels` are employed by the `ColourSelectionWidget`. An example for
            which this option is useful is in the case we wish to create
            rendering options for multiple :map:`LandmarkGroup` objects and
            each one of them has a different set of `labels`. If ``None``, then
            `labels_per_object` is a `list` of lenth `n_objects` with ``None``.
        selected_object : `int`, optional
            The object for which to show the rendering options in the beginning,
            when the widget is created.
        object_selection_dropdown_visible : `bool`, optional
            Controls the visibility of the object selection dropdown
            (`self.object_selection_dropdown`).
        allow_callback : `bool`, optional
            If ``True``, it allows triggering of any callback functions.
        """
        # Check options
        if selected_object is None:
            selected_object = self.object_selection_dropdown.value
        if object_selection_dropdown_visible is not None:
            self.object_selection_dropdown.visible = \
                self._selection_dropdown_visible(
                    object_selection_dropdown_visible)
            self.object_selection_dropdown_visible = \
                object_selection_dropdown_visible

        # Update sub-options widgets
        for i, tab in enumerate(self.options_tabs):
            # get the options to pass to the sub-options update functions
            if tab == 'figure_one' or tab == 'figure_two':
                tmp_options = renderer_options[selected_object]['figure']
            else:
                tmp_options = renderer_options[selected_object][tab]
            # call sub-options classes
            if tab == 'lines' or tab == 'markers':
                self.options_widgets[i].set_widget_state(
                    tmp_options, labels=labels_per_object[selected_object],
                    allow_callback=False)
            else:
                self.options_widgets[i].set_widget_state(
                    tmp_options, allow_callback=False)

        # Assign new options dict to selected_values
        self.selected_values = renderer_options
        self.labels_per_object = labels_per_object

        # trigger render function if allowed
        if allow_callback:
            self._render_function('', True)

    def update_object_names(self, objects_names):
        r"""
        Method that updates the options in the dropdown menu for selecting an
        object. Note that the number of objects should not change.

        Parameters
        ----------
        objects_names : `list` of `str`
            A `list` with the names of the objects that will be used in the
            selection dropdown menu.
        """
        if not self.objects_names == objects_names:
            # update dropdown options
            objects_dict = OrderedDict()
            for k, g in enumerate(objects_names):
                objects_dict[g] = k
            self.object_selection_dropdown.options = objects_dict
            self.objects_names = objects_names

            # make sure the dropdown gets updated
            tmp = self.object_selection_dropdown.value
            if self.object_selection_dropdown.value > 0:
                self.object_selection_dropdown.value = 0
                self.object_selection_dropdown.value = tmp
            elif (self.object_selection_dropdown.value == 0 and
                  len(self.object_selection_dropdown.options) > 1):
                self.object_selection_dropdown.value = 1
                self.object_selection_dropdown.value = 0


class GraphOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for selecting options for rendering various curves in a
    graph. The widget consists of the following parts from
    `IPython.html.widgets` and `menpowidgets.tools`:

    == ===================== ======================= =======================
    No Object                Variable (`self.`)      Description
    == ===================== ======================= =======================
    1  RendererOptionsWidget `renderer_widget`       The rendering widget
    2  FloatRangeSlider      `x_limit`               Sets the x limit
    3  FloatRangeSlider      `y_limit`               Sets the y limit
    4  Text                  `x_label`               Sets the x label
    5  Text                  `y_label`               Sets the y label
    6  Text                  `title`                 Sets the title
    7  Textarea              `legend_entries`        Sets the legend entries
    8  VBox                  `graph_related_options` Contains 2 - 7
    9  Tab                   `options_tab`           Contains 8, 1
    == ===================== ======================= =======================

    Note that:

    * The selected values are stored in the ``self.selected_values`` `dict`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` methods.

    Parameters
    ----------
    graph_options : `list` of `str`
        The initial options. For example, in case we had two curves to render
        ::

            graph_options = {'legend_entries': ['Nontas', 'Leda'],
                             'x_label': 'X',
                             'y_label': 'Y',
                             'title': 'TITLE',
                             'x_axis_limits': (2, 7),
                             'y_axis_limits': (-0.2, 0.2),
                             'render_lines': [True, True],
                             'line_colour': ['r', 'b'],
                             'line_style': ['--', '-'],
                             'line_width': [1, 3],
                             'render_markers': [True, False],
                             'marker_style': ['o', 's'],
                             'marker_size': [6, 12],
                             'marker_face_colour': ['k', 'm'],
                             'marker_edge_colour': ['w', 'c'],
                             'marker_edge_width': [1, 4],
                             'render_legend': True,
                             'legend_title': '',
                             'legend_font_name': 'sans-serif',
                             'legend_font_style': 'normal',
                             'legend_font_size': 10,
                             'legend_font_weight': 'normal',
                             'legend_marker_scale': 1.,
                             'legend_location': 2,
                             'legend_bbox_to_anchor': (1.05, 1.),
                             'legend_border_axes_pad': 0.,
                             'legend_n_columns': 1,
                             'legend_horizontal_spacing': 0,
                             'legend_vertical_spacing': 0,
                             'legend_border': True,
                             'legend_border_padding': 0,
                             'legend_shadow': False,
                             'legend_rounded_corners': False,
                             'render_axes': True,
                             'axes_font_name': 'sans-serif',
                             'axes_font_size': 10,
                             'axes_font_style': 'normal',
                             'axes_font_weight': 'normal',
                             'figure_size': (10, 8),
                             'render_grid': True,
                             'grid_line_style': '--',
                             'grid_line_width': 1}

    x_slider_options : (`float`, `float`, `float`)
        The attributes of the x limit slider in the form (`min`, `max`, `step`).
    y_slider_options : (`float`, `float`, `float`)
        The attributes of the y limit slider in the form (`min`, `max`, `step`).
    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    tabs_style : See Below, optional
        Sets a predefined style at the tabs of the widget. Possible options
        are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    renderer_tabs_style : See Below, optional
        Sets a predefined style at the tabs of the renderer widget. Possible
        options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    """
    def __init__(self, graph_options, x_slider_options, y_slider_options,
                 render_function=None, style='minimal', tabs_style='minimal',
                 renderer_tabs_style='minimal'):
        # Get number of curves (objects)
        if graph_options['legend_entries'] is None:
            raise ValueError("legend_entries must be a list, not None")
        self.n_curves = len(graph_options['legend_entries'])

        # Check options
        graph_options['render_lines'] = \
            self._check_option(graph_options['render_lines'])
        graph_options['line_style'] = \
            self._check_option(graph_options['line_style'])
        graph_options['line_width'] = \
            self._check_option(graph_options['line_width'])
        graph_options['render_markers'] = \
            self._check_option(graph_options['render_markers'])
        graph_options['marker_style'] = \
            self._check_option(graph_options['marker_style'])
        graph_options['marker_size'] = \
            self._check_option(graph_options['marker_size'])
        graph_options['marker_edge_width'] = \
            self._check_option(graph_options['marker_edge_width'])
        self.initial_figure_size = graph_options['figure_size']

        # Create renderer dictionaries
        renderer_options = []
        legend_options = {
            'render_legend': graph_options['render_legend'],
            'legend_title': graph_options['legend_title'],
            'legend_font_name': graph_options['legend_font_name'],
            'legend_font_style': graph_options['legend_font_style'],
            'legend_font_size': graph_options['legend_font_size'],
            'legend_font_weight': graph_options['legend_font_weight'],
            'legend_marker_scale': graph_options['legend_marker_scale'],
            'legend_location': graph_options['legend_location'],
            'legend_bbox_to_anchor': graph_options['legend_bbox_to_anchor'],
            'legend_border_axes_pad': graph_options['legend_border_axes_pad'],
            'legend_n_columns': graph_options['legend_n_columns'],
            'legend_horizontal_spacing':
            graph_options['legend_horizontal_spacing'],
            'legend_vertical_spacing': graph_options['legend_vertical_spacing'],
            'legend_border': graph_options['legend_border'],
            'legend_border_padding': graph_options['legend_border_padding'],
            'legend_shadow': graph_options['legend_shadow'],
            'legend_rounded_corners': graph_options['legend_rounded_corners']}
        figure_options = {'x_scale': 1., 'y_scale': 1.,
                          'render_axes': graph_options['render_axes'],
                          'axes_font_name': graph_options['axes_font_name'],
                          'axes_font_size': graph_options['axes_font_size'],
                          'axes_font_style': graph_options['axes_font_style'],
                          'axes_font_weight': graph_options['axes_font_weight'],
                          'axes_x_limits': None,
                          'axes_y_limits': None}
        grid_options = {'render_grid': graph_options['render_grid'],
                        'grid_line_style': graph_options['grid_line_style'],
                        'grid_line_width': graph_options['grid_line_width']}
        for i in range(self.n_curves):
            lines_options = {'render_lines': graph_options['render_lines'][i],
                             'line_width': graph_options['line_width'][i],
                             'line_colour': [graph_options['line_colour'][i]],
                             'line_style': graph_options['line_style'][i]}
            markers_options = {
                'render_markers': graph_options['render_markers'][i],
                'marker_size': graph_options['marker_size'][i],
                'marker_face_colour': [graph_options['marker_face_colour'][i]],
                'marker_edge_colour': [graph_options['marker_edge_colour'][i]],
                'marker_style': graph_options['marker_style'][i],
                'marker_edge_width': graph_options['marker_edge_width'][i]}
            rendering_dict = {'lines': lines_options,
                              'markers': markers_options,
                              'legend': legend_options,
                              'figure': figure_options,
                              'grid': grid_options}
            renderer_options.append(rendering_dict)

        # Create widgets
        options_tabs = ['lines', 'markers', 'legend', 'figure_two', 'grid']
        self.renderer_widget = RendererOptionsWidget(
            renderer_options, options_tabs=options_tabs,
            objects_names=graph_options['legend_entries'],
            object_selection_dropdown_visible=self.n_curves > 1,
            render_function=None)
        # Make the x and y limits of the axes widget invisible. They will be
        # controlled by the sliders in the graph options.
        self.renderer_widget.options_widgets[3].axes_x_limits_box.visible = \
            False
        self.renderer_widget.options_widgets[3].axes_y_limits_box.visible = \
            False
        self.x_limit = ipywidgets.FloatRangeSlider(
            min=x_slider_options[0], max=x_slider_options[1],
            step=x_slider_options[2], value=graph_options['x_axis_limits'],
            description='X limits', margin='0.05cm', width='7.3cm')
        self.y_limit = ipywidgets.FloatRangeSlider(
            min=y_slider_options[0], max=y_slider_options[1],
            step=y_slider_options[2], value=graph_options['y_axis_limits'],
            description='Y limits', margin='0.05cm', width='7.3cm')
        self.x_label = ipywidgets.Text(description='X label', margin='0.05cm',
                                       value=graph_options['x_label'])
        self.y_label = ipywidgets.Text(description='Y label', margin='0.05cm',
                                       value=graph_options['y_label'])
        self.title = ipywidgets.Text(description='Title', margin='0.05cm',
                                     value=graph_options['title'])
        self.legend_entries = ipywidgets.Textarea(
            description='Legend', width='73mm', margin='0.05cm',
            value=self._convert_list_to_legend_entries(
                graph_options['legend_entries']))
        self.graph_related_options = ipywidgets.VBox(
            children=[self.x_limit, self.y_limit, self.x_label, self.y_label,
                      self.title, self.legend_entries])
        self.options_tab = ipywidgets.Tab(
            children=[self.graph_related_options, self.renderer_widget])
        self.options_tab.set_title(0, 'Graph')
        self.options_tab.set_title(1, 'Renderer')
        super(GraphOptionsWidget, self).__init__(children=[self.options_tab])

        # Assign output
        self.selected_values = graph_options

        # Set style
        self.predefined_style(style, tabs_style, renderer_tabs_style)

        # Set functionality
        def legend_entries_function(name, value):
            tmp_entries = str(self.legend_entries.value).splitlines()
            if len(tmp_entries) < self.n_curves:
                n_missing = self.n_curves - len(tmp_entries)
                for j in range(n_missing):
                    kk = j + len(tmp_entries)
                    tmp_entries.append("curve {}".format(kk))
            self.selected_values['legend_entries'] = tmp_entries[:self.n_curves]
        self.legend_entries.on_trait_change(legend_entries_function, 'value')

        def update_renderer_widget_objects(name, value):
            self.renderer_widget.update_object_names(
                self.selected_values['legend_entries'])
        self.options_tab.on_trait_change(update_renderer_widget_objects,
                                         'selected_index')

        def get_graph_related_options(name, value):
            self.selected_values['x_label'] = str(self.x_label.value)
            self.selected_values['y_label'] = str(self.y_label.value)
            self.selected_values['title'] = str(self.title.value)
            self.selected_values['x_axis_limits'] = self.x_limit.value
            self.selected_values['y_axis_limits'] = self.y_limit.value
        self.x_label.on_trait_change(get_graph_related_options, 'value')
        self.y_label.on_trait_change(get_graph_related_options, 'value')
        self.title.on_trait_change(get_graph_related_options, 'value')
        self.x_limit.on_trait_change(get_graph_related_options, 'value')
        self.y_limit.on_trait_change(get_graph_related_options, 'value')

        # Set render function
        self._render_function = None
        self.add_render_function(render_function)

    def _check_option(self, val):
        if isinstance(val, list) and not len(val) == self.n_curves:
            raise ValueError("lines and markers related options must be lists "
                             "of length equal to the number of curves.")
        elif val is None:
            raise ValueError("lines and markers related options cannot be None")
        elif val is not None and not isinstance(val, list):
            val = [val] * self.n_curves
        return val

    def _convert_list_to_legend_entries(self, l):
        tmp_lines = []
        for k in l:
            tmp_lines.append(k)
            tmp_lines.append('\n')
        tmp_lines = tmp_lines[:-1]
        return unicode().join(tmp_lines)

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0,
              padding='0.2cm', margin=0, tabs_box_style=None,
              tabs_border_visible=True, tabs_border_color='black',
              tabs_border_style='solid', tabs_border_width=1,
              tabs_border_radius=1, tabs_padding=0, tabs_margin=0,
              renderer_tabs_box_style=None, renderer_tabs_border_visible=True,
              renderer_tabs_border_color='black',
              renderer_tabs_border_style='solid',
              renderer_tabs_border_width=1, renderer_tabs_border_radius=1,
              renderer_tabs_padding=0, renderer_tabs_margin=0,
              font_family='', font_size=None, font_style='', font_weight=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        tabs_box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        tabs_border_visible : `bool`, optional
            Defines whether to draw the border line around the tab widgets.
        tabs_border_color : `str`, optional
            The color of the border around the tab widgets.
        tabs_border_style : `str`, optional
            The line style of the border around the tab widgets.
        tabs_border_width : `float`, optional
            The line width of the border around the tab widgets.
        tabs_border_radius : `float`, optional
            The radius of the corners of the box of the tab widgets.
        tabs_padding : `float`, optional
            The padding around the tab widgets.
        tabs_margin : `float`, optional
            The margin around the tab widgets.

        renderer_tabs_box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        renderer_tabs_border_visible : `bool`, optional
            Defines whether to draw the border line around the tab widgets of
            the renderer widget.
        renderer_tabs_border_color : `str`, optional
            The color of the border around the tab widgets of the renderer
            widget.
        renderer_tabs_border_style : `str`, optional
            The line style of the border around the tab widgets of the renderer
            widget.
        renderer_tabs_border_width : `float`, optional
            The line width of the border around the tab widgets of the renderer
            widget.
        renderer_tabs_border_radius : `float`, optional
            The radius of the corners of the box of the tab widgets of the
            renderer widget.
        renderer_tabs_padding : `float`, optional
            The padding around the tab widgets of the renderer widget.
        renderer_tabs_margin : `float`, optional
            The margin around the tab widgets of the renderer widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_box(self.graph_related_options, tabs_box_style,
                   tabs_border_visible, tabs_border_color, tabs_border_style,
                   tabs_border_width, tabs_border_radius, tabs_padding,
                   tabs_margin)
        self.x_limit.slider_color = map_styles_to_hex_colours(tabs_box_style)
        self.x_limit.background_color = map_styles_to_hex_colours(tabs_box_style)
        self.y_limit.slider_color = map_styles_to_hex_colours(tabs_box_style)
        self.y_limit.background_color = map_styles_to_hex_colours(tabs_box_style)
        format_box(self.renderer_widget, tabs_box_style, tabs_border_visible,
                   tabs_border_color, tabs_border_style, tabs_border_width,
                   tabs_border_radius, tabs_padding, tabs_margin)
        for wid in self.renderer_widget.options_widgets:
            wid.style(box_style=renderer_tabs_box_style,
                      border_visible=renderer_tabs_border_visible,
                      border_color=renderer_tabs_border_color,
                      border_style=renderer_tabs_border_style,
                      border_width=renderer_tabs_border_width,
                      border_radius=renderer_tabs_border_radius,
                      padding=renderer_tabs_padding,
                      margin=renderer_tabs_margin, font_family=font_family,
                      font_size=font_size, font_style=font_style,
                      font_weight=font_weight)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.renderer_widget.object_selection_dropdown,
                    font_family, font_size, font_style, font_weight)
        format_font(self.graph_related_options, font_family, font_size,
                    font_style, font_weight)
        format_font(self.x_limit, font_family, font_size, font_style,
                    font_weight)
        format_font(self.y_limit, font_family, font_size, font_style,
                    font_weight)
        format_font(self.x_label, font_family, font_size, font_style,
                    font_weight)
        format_font(self.y_label, font_family, font_size, font_style,
                    font_weight)
        format_font(self.title, font_family, font_size, font_style,
                    font_weight)
        format_font(self.legend_entries, font_family, font_size, font_style,
                    font_weight)

    def predefined_style(self, style, tabs_style='minimal',
                         renderer_tabs_style='mininal'):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================

        tabs_style : `str` (see below), optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================

        renderer_tabs_style : `str` (see below), optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if renderer_tabs_style == 'minimal' or renderer_tabs_style == '':
            renderer_tabs_style = ''
            renderer_tabs_border_visible = False
            renderer_tabs_border_color = 'black'
            renderer_tabs_border_radius = 0
            renderer_tabs_padding = 0
        else:
            renderer_tabs_style = renderer_tabs_style
            renderer_tabs_border_visible = True
            renderer_tabs_border_color = \
                map_styles_to_hex_colours(renderer_tabs_style)
            renderer_tabs_border_radius = 10
            renderer_tabs_padding = '0.3cm'

        if tabs_style == 'minimal' or tabs_style == '':
            tabs_style = ''
            tabs_border_visible = True
            tabs_border_color = 'black'
            tabs_border_radius = 0
            tabs_padding = 0
        else:
            tabs_style = tabs_style
            tabs_border_visible = True
            tabs_border_color = map_styles_to_hex_colours(tabs_style)
            tabs_border_radius = 10
            tabs_padding = '0.2cm'

        if style == 'minimal':
            self.style(box_style='', border_visible=True, border_color='black',
                       border_style='solid', border_width=1, border_radius=0,
                       padding='0.2cm', margin='0.5cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       tabs_box_style=tabs_style,
                       tabs_border_visible=tabs_border_visible,
                       tabs_border_color=tabs_border_color,
                       tabs_border_style='solid', tabs_border_width=1,
                       tabs_border_radius=tabs_border_radius,
                       tabs_padding=tabs_padding, tabs_margin='0.3cm',
                       renderer_tabs_box_style=renderer_tabs_style,
                       renderer_tabs_border_visible=renderer_tabs_border_visible,
                       renderer_tabs_border_color=renderer_tabs_border_color,
                       renderer_tabs_border_style='solid',
                       renderer_tabs_border_width=1,
                       renderer_tabs_border_radius=renderer_tabs_border_radius,
                       renderer_tabs_padding=renderer_tabs_padding,
                       renderer_tabs_margin='0.5cm')
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.5cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       tabs_box_style=tabs_style,
                       tabs_border_visible=tabs_border_visible,
                       tabs_border_color=tabs_border_color,
                       tabs_border_style='solid', tabs_border_width=1,
                       tabs_border_radius=tabs_border_radius,
                       tabs_padding=tabs_padding, tabs_margin='0.3cm',
                       renderer_tabs_box_style=renderer_tabs_style,
                       renderer_tabs_border_visible=renderer_tabs_border_visible,
                       renderer_tabs_border_color=renderer_tabs_border_color,
                       renderer_tabs_border_style='solid',
                       renderer_tabs_border_width=1,
                       renderer_tabs_border_radius=renderer_tabs_border_radius,
                       renderer_tabs_padding=renderer_tabs_padding,
                       renderer_tabs_margin='0.5cm')
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def _get_selected_options(self):
        # legend options
        legend_tmp = self.renderer_widget.selected_values[0]['legend']
        self.selected_values.update(legend_tmp)

        # axes options
        figure_tmp = self.renderer_widget.selected_values[0]['figure']
        self.selected_values['render_axes'] = figure_tmp['render_axes']
        self.selected_values['axes_font_name'] = figure_tmp['axes_font_name']
        self.selected_values['axes_font_size'] = figure_tmp['axes_font_size']
        self.selected_values['axes_font_style'] = figure_tmp['axes_font_style']
        self.selected_values['axes_font_weight'] = \
            figure_tmp['axes_font_weight']
        self.selected_values['figure_size'] = \
            (figure_tmp['x_scale'] * self.initial_figure_size[0],
             figure_tmp['y_scale'] * self.initial_figure_size[1])

        # grid options
        grid_tmp = self.renderer_widget.selected_values[0]['grid']
        self.selected_values.update(grid_tmp)

        # lines and markers options
        for j in range(self.n_curves):
            self.selected_values['render_lines'][j] = \
                self.renderer_widget.selected_values[j]['lines']['render_lines']
            self.selected_values['line_colour'][j] = \
                self.renderer_widget.selected_values[j]['lines']['line_colour'][0]
            self.selected_values['line_style'][j] = \
                self.renderer_widget.selected_values[j]['lines']['line_style']
            self.selected_values['line_width'][j] = \
                self.renderer_widget.selected_values[j]['lines']['line_width']
            self.selected_values['render_markers'][j] = \
                self.renderer_widget.selected_values[j]['markers']['render_markers']
            self.selected_values['marker_style'][j] = \
                self.renderer_widget.selected_values[j]['markers']['marker_style']
            self.selected_values['marker_size'][j] = \
                self.renderer_widget.selected_values[j]['markers']['marker_size']
            self.selected_values['marker_face_colour'][j] = \
                self.renderer_widget.selected_values[j]['markers']['marker_face_colour'][0]
            self.selected_values['marker_edge_colour'][j] = \
                self.renderer_widget.selected_values[j]['markers']['marker_edge_colour'][0]
            self.selected_values['marker_edge_width'][j] = \
                self.renderer_widget.selected_values[j]['markers']['marker_edge_width']

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function_tmp = render_function
        if self._render_function_tmp is None:
            def render_function_with_get_options(name, value):
                # Get all the selected values
                self._get_selected_options()
                # Make displacements menu invisible
                self.plot_displacements_menu.visible = False
        else:
            def render_function_with_get_options(name, value):
                # Get all the selected values
                self._get_selected_options()
                # Call render function
                self._render_function_tmp(name, value)
        self._render_function = render_function_with_get_options
        self.renderer_widget.add_render_function(self._render_function)
        self.x_limit.on_trait_change(self._render_function, 'value')
        self.y_limit.on_trait_change(self._render_function, 'value')
        self.x_label.on_trait_change(self._render_function, 'value')
        self.y_label.on_trait_change(self._render_function, 'value')
        self.title.on_trait_change(self._render_function, 'value')
        self.legend_entries.on_trait_change(self._render_function, 'value')

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        self.renderer_widget.remove_render_function()
        self.x_limit.on_trait_change(self._render_function, 'value',
                                     remove=True)
        self.y_limit.on_trait_change(self._render_function, 'value',
                                     remove=True)
        self.x_label.on_trait_change(self._render_function, 'value',
                                     remove=True)
        self.y_label.on_trait_change(self._render_function, 'value',
                                     remove=True)
        self.title.on_trait_change(self._render_function, 'value', remove=True)
        self.legend_entries.on_trait_change(self._render_function, 'value',
                                            remove=True)
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)


class SaveFigureOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for saving a figure to file. The widget consists of the
    following parts from `IPython.html.widgets` and
    `menpowidgets.tools`:

    == ===================== ====================== ==========================
    No Object                Variable (`self.`)     Description
    == ===================== ====================== ==========================
    1  Select                `file_format_select`   Image format selector
    2  FloatText             `dpi_text`             DPI selector
    3  Dropdown              `orientation_dropdown` Paper orientation selector
    4  Select                `papertype_select`     Paper type selector
    5  Checkbox              `transparent_checkbox` Transparency setter
    6  ColourSelectionWidget `facecolour_widget`    Face colour selector
    7  ColourSelectionWidget `edgecolour_widget`    Edge colour selector
    8  FloatText             `pad_inches_text`      Padding in inches setter
    9  Text                  `filename_text`        Path and filename
    10 Checkbox              `overwrite_checkbox`   Overwrite flag
    11 Latex                 `error_latex`          Error message area
    12 Button                `save_button`          Save button
    13 VBox                  `path_box`             Contains 9, 1, 10, 4
    14 VBox                  `page_box`             Contains 3, 2, 8
    15 VBox                  `colour_box`           Contains 6, 7, 5
    16 Tab                   `options_tabs`         Contains 13, 14, 15
    17 HBox                  `save_box`             Contains 12, 11
    18 VBox                  `options_box`          Contains 16, 17
    == ===================== ====================== ==========================

    To set the styling please refer to the ``style()`` and
    ``predefined_style()`` methods.

    Parameters
    ----------
    renderer : :map:`Renderer` class or subclass
        The renderer object that was used to render the figure.
    file_format : `str`, optional
        The initial value of the file format.
    dpi : `float` or ``None``, optional
        The initial value of the dpi. If ``None``, then dpi is set to ``0``.
    orientation : {``'portrait'``, ``'landscape'``}, optional
        The initial value of the orientation.
    papertype : `str`, optional
        The initial value of the paper type.
        Possible options are ::

            {'letter', 'legal', 'executive', 'ledger', 'a0', 'a1', 'a2', 'a3',
             'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10', 'b0', 'b1', 'b2', 'b3',
             'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10'}

    transparent : `bool`, optional
        The initial value of the transparency flag.
    facecolour : `str` or `list` of `float`, optional
        The initial value of the face colour.
    edgecolour : `str` or `list` of `float`, optional
        The initial value of the edge colour.
    pad_inches : `float`, optional
        The initial value of the figure padding in inches.
    overwrite : `bool`, optional
        The initial value of the overwrite flag.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================
    """
    def __init__(self, renderer, file_format='png', dpi=None,
                 orientation='portrait', papertype='letter', transparent=False,
                 facecolour='w', edgecolour='w', pad_inches=0.,
                 overwrite=False, style='minimal'):
        from os import getcwd
        from os.path import join, splitext

        # Create widgets
        file_format_dict = OrderedDict()
        file_format_dict['png'] = 'png'
        file_format_dict['jpg'] = 'jpg'
        file_format_dict['pdf'] = 'pdf'
        file_format_dict['eps'] = 'eps'
        file_format_dict['postscript'] = 'ps'
        file_format_dict['svg'] = 'svg'
        self.file_format_select = ipywidgets.Select(
            options=file_format_dict, value=file_format, description='Format',
            width='3cm')
        if dpi is None:
            dpi = 0
        self.dpi_text = ipywidgets.FloatText(description='DPI', value=dpi)
        orientation_dict = OrderedDict()
        orientation_dict['portrait'] = 'portrait'
        orientation_dict['landscape'] = 'landscape'
        self.orientation_dropdown = ipywidgets.Dropdown(
            options=orientation_dict, value=orientation,
            description='Orientation')
        papertype_dict = OrderedDict()
        papertype_dict['letter'] = 'letter'
        papertype_dict['legal'] = 'legal'
        papertype_dict['executive'] = 'executive'
        papertype_dict['ledger'] = 'ledger'
        papertype_dict['a0'] = 'a0'
        papertype_dict['a1'] = 'a1'
        papertype_dict['a2'] = 'a2'
        papertype_dict['a3'] = 'a3'
        papertype_dict['a4'] = 'a4'
        papertype_dict['a5'] = 'a5'
        papertype_dict['a6'] = 'a6'
        papertype_dict['a7'] = 'a7'
        papertype_dict['a8'] = 'a8'
        papertype_dict['a9'] = 'a9'
        papertype_dict['a10'] = 'a10'
        papertype_dict['b0'] = 'b0'
        papertype_dict['b1'] = 'b1'
        papertype_dict['b2'] = 'b2'
        papertype_dict['b3'] = 'b3'
        papertype_dict['b4'] = 'b4'
        papertype_dict['b5'] = 'b5'
        papertype_dict['b6'] = 'b6'
        papertype_dict['b7'] = 'b7'
        papertype_dict['b8'] = 'b8'
        papertype_dict['b9'] = 'b9'
        papertype_dict['b10'] = 'b10'
        self.papertype_select = ipywidgets.Select(
            options=papertype_dict, value=papertype, description='Paper type',
            visible=file_format == 'ps', width='3cm')
        self.transparent_checkbox = ipywidgets.Checkbox(
            description='Transparent', value=transparent)
        self.facecolour_widget = ColourSelectionWidget(
            [facecolour], description='Face colour')
        self.edgecolour_widget = ColourSelectionWidget(
            [edgecolour], description='Edge colour')
        self.pad_inches_text = ipywidgets.FloatText(description='Pad (inch)',
                                                    value=pad_inches)
        self.filename_text = ipywidgets.Text(
            description='Path', value=join(getcwd(), 'Untitled.' + file_format),
            width='10cm')
        self.overwrite_checkbox = ipywidgets.Checkbox(
            description='Overwrite if file exists', value=overwrite)
        self.error_latex = ipywidgets.Latex(value="", font_weight='bold',
                                            font_style='italic')
        self.save_button = ipywidgets.Button(description='Save',
                                             margin='0.2cm')

        # Group widgets
        self.path_box = ipywidgets.VBox(
            children=[self.filename_text, self.file_format_select,
                      self.papertype_select, self.overwrite_checkbox],
            align='end', margin='0.2cm')
        self.page_box = ipywidgets.VBox(
            children=[self.orientation_dropdown, self.dpi_text,
                      self.pad_inches_text], margin='0.2cm')
        self.colour_box = ipywidgets.VBox(
            children=[self.facecolour_widget, self.edgecolour_widget,
                      self.transparent_checkbox], margin='0.2cm')
        self.options_tabs = ipywidgets.Tab(
            children=[self.path_box, self.page_box, self.colour_box],
            margin=0, padding='0.1cm')
        self.options_tabs_box = ipywidgets.Box(
            children=[self.options_tabs], border_width=1, border_color='black',
            margin='0.3cm', padding='0.2cm')
        tab_titles = ['Path', 'Page setup', 'Image colour']
        for (k, tl) in enumerate(tab_titles):
            self.options_tabs.set_title(k, tl)
        self.save_box = ipywidgets.HBox(
            children=[self.save_button, self.error_latex], align='center')
        self.options_box = ipywidgets.VBox(
            children=[self.options_tabs, self.save_box], align='center')
        super(SaveFigureOptionsWidget, self).__init__(
            children=[self.options_box])
        self.align = 'start'

        # Assign renderer
        self.renderer = renderer

        # Set style
        self.predefined_style(style)

        # Set functionality
        def papertype_visibility(name, value):
            self.papertype_select.visible = value == 'ps'
        self.file_format_select.on_trait_change(papertype_visibility, 'value')

        def set_extension(name, value):
            file_name, file_extension = splitext(self.filename_text.value)
            self.filename_text.value = file_name + '.' + value
        self.file_format_select.on_trait_change(set_extension, 'value')

        def save_function(name):
            # set save button state
            self.error_latex.value = ''
            self.save_button.description = 'Saving...'
            self.save_button.disabled = True

            # save figure
            selected_dpi = self.dpi_text.value
            if self.dpi_text.value == 0:
                selected_dpi = None
            try:
                self.renderer.save_figure(
                    filename=self.filename_text.value, dpi=selected_dpi,
                    face_colour=
                    self.facecolour_widget.selected_values['colour'][0],
                    edge_colour=
                    self.edgecolour_widget.selected_values['colour'][0],
                    orientation=self.orientation_dropdown.value,
                    paper_type=self.papertype_select.value,
                    format=self.file_format_select.value,
                    transparent=self.transparent_checkbox.value,
                    pad_inches=self.pad_inches_text.value,
                    overwrite=self.overwrite_checkbox.value)
                self.error_latex.value = ''
            except ValueError as e:
                if (e.message == 'File already exists. Please set the '
                                 'overwrite kwarg if you wish to overwrite '
                                 'the file.'):
                    self.error_latex.value = 'File exists! ' \
                                             'Tick overwrite to replace it.'
                else:
                    self.error_latex.value = e.message

            # set save button state
            self.save_button.description = 'Save'
            self.save_button.disabled = False
        self.save_button.on_click(save_function)

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.file_format_select, font_family, font_size, font_style,
                    font_weight)
        format_font(self.dpi_text, font_family, font_size, font_style,
                    font_weight)
        format_font(self.orientation_dropdown, font_family, font_size,
                    font_style, font_weight)
        format_font(self.papertype_select, font_family, font_size,  font_style,
                    font_weight)
        format_font(self.transparent_checkbox, font_family, font_size,
                    font_style, font_weight)
        format_font(self.pad_inches_text, font_family, font_size, font_style,
                    font_weight)
        format_font(self.filename_text, font_family, font_size, font_style,
                    font_weight)
        format_font(self.overwrite_checkbox, font_family, font_size, font_style,
                    font_weight)
        format_font(self.save_button, font_family, font_size, font_style,
                    font_weight)
        self.facecolour_widget.style(
            box_style=None, border_visible=False, font_family=font_family,
            font_size=font_size, font_weight=font_weight, font_style=font_style)
        self.edgecolour_widget.style(
            box_style=None, border_visible=False, font_family=font_family,
            font_size=font_size, font_weight=font_weight, font_style=font_style)

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style='', border_visible=True, border_color='black',
                       border_style='solid', border_width=1, border_radius=0,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='')
            self.save_button.button_style = ''
            self.save_button.font_weight = 'normal'
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color= map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='')
            self.save_button.button_style = 'primary'
            self.save_button.font_weight = 'bold'
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')


class FeatureOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for selecting feature options. Specifically, it consists
    of:

        1) RadioButtons [`self.feature_radiobuttons`]: select feature type
        2) DSIFTOptionsWidget [`self.dsift_options_widget`]: dsift options widget
        3) HOGOptionsWidget [`self.hog_options_widget`]: hog options widget
        4) IGOOptionsWidget [`self.igo_options_widget`]: igo options widget
        5) LBPOptionsWidget [`self.lbp_options_widget`]: lbp options widget
        6) DaisyOptionsWidget [`self.daisy_options_widget`]: daisy options
           widget
        7) Latex [`self.no_options_widget`]: message for no options available
        8) Box [`self.per_feature_options_box`]: box that contains (2), (3),
           (4), (5), (6) and (7)
        9) Image [`self.preview_image`]: lenna image
        10) Latex [`self.preview_input_latex`]: the initial image information
        11) Latex [`self.preview_output_latex`]: the output image information
        12) Latex [`self.preview_time_latex`]: the timing information
        13) VBox [`self.preview_box`]: box that contains (9), (10), (11), (12)
        14) Tab [`self.options_box`]: box that contains (1), (8) and (13)

    To set the styling of this widget please refer to the `style()` method. The
    widget stores the features `function` to `self.features_function`, the
    features options `dict` in `self.features_options` and the `partial`
    function with the options as `self.function`.

    Parameters
    ----------
    style : `str` (see below)
        Sets a predefined style at the widget. Possible options are ::

            {``'minimal'``, ``'success'``, ``'info'``, ``'warning'``,
             ``'danger'``, ``''``}

    """
    def __init__(self, style='minimal'):
        # import features methods and time
        import time
        from menpo.feature import (dsift, hog, lbp, igo, es, daisy, gradient,
                                   no_op)
        from menpo.image import Image
        import menpo.io as mio
        from menpo.feature.visualize import sum_channels

        # Create widgets
        tmp = OrderedDict()
        tmp['DSIFT'] = dsift
        tmp['HOG'] = hog
        tmp['IGO'] = igo
        tmp['ES'] = es
        tmp['Daisy'] = daisy
        tmp['LBP'] = lbp
        tmp['Gradient'] = gradient
        tmp['None'] = no_op
        self.feature_radiobuttons = ipywidgets.RadioButtons(
            value=no_op, options=tmp, description='Feature type:')
        dsift_options_dict = {'window_step_horizontal': 1,
                              'window_step_vertical': 1,
                              'num_bins_horizontal': 2, 'num_bins_vertical': 2,
                              'num_or_bins': 9, 'cell_size_horizontal': 6,
                              'cell_size_vertical': 6, 'fast': True}
        self.dsift_options_widget = DSIFTOptionsWidget(dsift_options_dict)
        self.dsift_options_widget.style(box_style=None, border_visible=False,
                                        margin='0.2cm')
        hog_options_dict = {'mode': 'dense', 'algorithm': 'dalaltriggs',
                            'num_bins': 9, 'cell_size': 8, 'block_size': 2,
                            'signed_gradient': True, 'l2_norm_clip': 0.2,
                            'window_height': 1, 'window_width': 1,
                            'window_unit': 'blocks', 'window_step_vertical': 1,
                            'window_step_horizontal': 1,
                            'window_step_unit': 'pixels', 'padding': True}
        self.hog_options_widget = HOGOptionsWidget(hog_options_dict)
        self.hog_options_widget.style(box_style=None, border_visible=False,
                                      margin='0.2cm')
        igo_options_dict = {'double_angles': True}
        self.igo_options_widget = IGOOptionsWidget(igo_options_dict)
        self.igo_options_widget.style(box_style=None, border_visible=False,
                                      margin='0.2cm')
        lbp_options_dict = {'radius': range(1, 5), 'samples': [8] * 4,
                            'mapping_type': 'u2', 'window_step_vertical': 1,
                            'window_step_horizontal': 1,
                            'window_step_unit': 'pixels', 'padding': True}
        self.lbp_options_widget = LBPOptionsWidget(lbp_options_dict)
        self.lbp_options_widget.style(box_style=None, border_visible=False,
                                      margin='0.2cm')
        daisy_options_dict = {'step': 1, 'radius': 15, 'rings': 2,
                              'histograms': 2, 'orientations': 8,
                              'normalization': 'l1', 'sigmas': None,
                              'ring_radii': None}
        self.daisy_options_widget = DaisyOptionsWidget(daisy_options_dict)
        self.daisy_options_widget.style(box_style=None, border_visible=False,
                                        margin='0.2cm')
        self.no_options_widget = ipywidgets.Latex(value='No options available.')

        # Load and rescale preview image (lenna)
        self.image = mio.import_builtin_asset.lenna_png()
        self.image.crop_to_landmarks_proportion_inplace(0.18)
        self.image = self.image.as_greyscale()

        # Group widgets
        self.per_feature_options_box = ipywidgets.Box(
            children=[self.dsift_options_widget, self.hog_options_widget,
                      self.igo_options_widget, self.lbp_options_widget,
                      self.daisy_options_widget, self.no_options_widget])
        self.preview_image = ipywidgets.Image(
            value=convert_image_to_bytes(self.image), visible=False)
        self.preview_input_latex = ipywidgets.Latex(
            value="Input: {}W x {}H x {}C".format(
                self.image.width, self.image.height, self.image.n_channels),
            visible=False)
        self.preview_output_latex = ipywidgets.Latex(value="")
        self.preview_time_latex = ipywidgets.Latex(value="")
        self.preview_box = ipywidgets.VBox(
            children=[self.preview_image, self.preview_input_latex,
                      self.preview_output_latex, self.preview_time_latex])
        self.options_box = ipywidgets.Tab(
            children=[self.feature_radiobuttons, self.per_feature_options_box,
                      self.preview_box])
        tab_titles = ['Feature', 'Options', 'Preview']
        for (k, tl) in enumerate(tab_titles):
            self.options_box.set_title(k, tl)
        super(FeatureOptionsWidget, self).__init__(children=[self.options_box])
        self.align = 'start'

        # Initialize output
        options = {}
        self.function = partial(no_op, **options)
        self.features_function = no_op
        self.features_options = options

        # Set style
        self.predefined_style(style)

        # Set functionality
        def per_feature_options_visibility(name, value):
            if value == dsift:
                self.igo_options_widget.visible = False
                self.lbp_options_widget.visible = False
                self.daisy_options_widget.visible = False
                self.no_options_widget.visible = False
                self.hog_options_widget.visible = False
                self.dsift_options_widget.visible = True
            elif value == hog:
                self.igo_options_widget.visible = False
                self.lbp_options_widget.visible = False
                self.daisy_options_widget.visible = False
                self.no_options_widget.visible = False
                self.dsift_options_widget.visible = False
                self.hog_options_widget.visible = True
            elif value == igo:
                self.hog_options_widget.visible = False
                self.lbp_options_widget.visible = False
                self.daisy_options_widget.visible = False
                self.no_options_widget.visible = False
                self.dsift_options_widget.visible = False
                self.igo_options_widget.visible = True
            elif value == lbp:
                self.hog_options_widget.visible = False
                self.igo_options_widget.visible = False
                self.daisy_options_widget.visible = False
                self.no_options_widget.visible = False
                self.dsift_options_widget.visible = False
                self.lbp_options_widget.visible = True
            elif value == daisy:
                self.hog_options_widget.visible = False
                self.igo_options_widget.visible = False
                self.lbp_options_widget.visible = False
                self.no_options_widget.visible = False
                self.dsift_options_widget.visible = False
                self.daisy_options_widget.visible = True
            else:
                self.hog_options_widget.visible = False
                self.igo_options_widget.visible = False
                self.lbp_options_widget.visible = False
                self.daisy_options_widget.visible = False
                self.dsift_options_widget.visible = False
                self.no_options_widget.visible = True
                for name, f in tmp.items():
                    if f == value:
                        self.no_options_widget.value = \
                            "{}: No available options.".format(name)
        self.feature_radiobuttons.on_trait_change(
            per_feature_options_visibility, 'value')
        per_feature_options_visibility('', no_op)

        def get_function(name, value):
            # get options
            if self.feature_radiobuttons.value == dsift:
                opts = self.dsift_options_widget.selected_values
            elif self.feature_radiobuttons.value == hog:
                opts = self.hog_options_widget.selected_values
            elif self.feature_radiobuttons.value == igo:
                opts = self.igo_options_widget.selected_values
            elif self.feature_radiobuttons.value == lbp:
                opts = self.lbp_options_widget.selected_values
            elif self.feature_radiobuttons.value == daisy:
                opts = self.daisy_options_widget.selected_values
            else:
                opts = {}
            # get features function closure
            func = partial(self.feature_radiobuttons.value, **opts)
            # store function
            self.function = func
            self.features_function = value
            self.features_options = opts
        self.feature_radiobuttons.on_trait_change(get_function, 'value')
        self.options_box.on_trait_change(get_function, 'selected_index')

        def preview_function(name, old_value, value):
            if value == 2:
                # extracting features message
                for name, f in tmp.items():
                    if f == self.function.func:
                        val1 = name
                self.preview_output_latex.value = \
                    "Previewing {} features...".format(val1)
                self.preview_time_latex.value = ""
                # extract feature and time it
                t = time.time()
                feat_image = self.function(self.image)
                t = time.time() - t
                # store feature image shape and n_channels
                val2 = feat_image.width
                val3 = feat_image.height
                val4 = feat_image.n_channels
                # compute sum of feature image and normalize its pixels in range
                # (0, 1) because it is required by as_PILImage
                feat_image = sum_channels(feat_image, channels=None)
                # feat_image = np.sum(feat_image.pixels, axis=2)
                feat_image = feat_image.pixels
                feat_image -= np.min(feat_image)
                feat_image /= np.max(feat_image)
                feat_image = Image(feat_image)
                # update preview
                self.preview_image.value = convert_image_to_bytes(feat_image)
                self.preview_input_latex.visible = True
                self.preview_image.visible = True
                # set info
                self.preview_output_latex.value = \
                    "{}: {}W x {}H x {}C".format(val1, val2, val3, val4)
                self.preview_time_latex.value = "{0:.2f} secs elapsed".format(t)
            if old_value == 2:
                self.preview_input_latex.visible = False
                self.preview_image.visible = False
        self.options_box.on_trait_change(preview_function, 'selected_index')

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.feature_radiobuttons, font_family, font_size,
                    font_style, font_weight)
        format_font(self.no_options_widget, font_family, font_size, font_style,
                    font_weight)
        format_font(self.preview_input_latex, font_family, font_size,
                    font_style, font_weight)
        format_font(self.preview_output_latex, font_family, font_size,
                    font_style, font_weight)
        format_font(self.preview_time_latex, font_family, font_size, font_style,
                    font_weight)
        self.dsift_options_widget.style(
            box_style=None, border_visible=False, margin='0.2cm',
            font_family=font_family, font_size=font_size, font_style=font_style,
            font_weight=font_weight)
        self.hog_options_widget.style(
            box_style=None, border_visible=False, margin='0.2cm',
            font_family=font_family, font_size=font_size, font_style=font_style,
            font_weight=font_weight)
        self.igo_options_widget.style(
            box_style=None, border_visible=False, margin='0.2cm',
            font_family=font_family, font_size=font_size, font_style=font_style,
            font_weight=font_weight)
        self.lbp_options_widget.style(
            box_style=None, border_visible=False, margin='0.2cm',
            font_family=font_family, font_size=font_size, font_style=font_style,
            font_weight=font_weight)
        self.daisy_options_widget.style(
            box_style=None, border_visible=False, margin='0.2cm',
            font_family=font_family, font_size=font_size, font_style=font_style,
            font_weight=font_weight)
        self.no_options_widget.margin = '0.2cm'

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style='', border_visible=True, border_color='black',
                       border_style='solid', border_width=1, border_radius=0,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='')
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color= map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='')
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')


class PatchOptionsWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for selecting patches options when rendering a patch-based
    image. The widget consists of the following parts from
    `IPython.html.widgets`:

    == ==================== ========================= ======================
    No Object               Variable (`self.`)        Description
    == ==================== ========================= ======================
    1  Dropdown             `offset_dropdown`         Offset index selection
    2  SlicingCommandWidget `slicing_wid`             Patch index selection
    3  LineOptionsWidget    `bboxes_line_options_wid` Bboxes options
    4  Checkbox             `render_centers`          Render centers flag
    5  Checkbox             `render_patches`          Render patches flag
    6  ToggleButton         `background_toggle`       Background colour button
    7  Latex                `background_title`        Background colour title
    8  HBox                 `background_box`          Contains 7, 6
    9  VBox                 `render_checkboxes_box`   Contains 4, 5
    10 HBox                 `render_box`              Contains 8, 9
    11 VBox                 `offset_patches_box`      Contains 1, 2, 10
    == ==================== ========================= ======================

    Note that:

    * The selected values are stored in the ``self.selected_values`` `dict`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` method.

    Parameters
    ----------
    patch_options : `dict`
        The dictionary with the initial options. For example
        ::

            patch_options = {'patches': {'command': '',
                                         'indices': [],
                                         'length': 68},
                             'offset_index': 0,
                             'n_offsets': 5,
                             'render_centers': True,
                             'render_centers': True,
                             'background': 'white',
                             'bboxes': {'render_lines': True,
                                        'line_colour': ['r'],
                                        'line_style': '-',
                                        'line_width': 1}
                            }

    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    style : See Below, optional
        Sets a predefined style at the widget's background. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    substyle : See Below, optional
        Sets a predefined style at the widget's patches and bboxes options.
        Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create a patches widget and then update its state. Firstly, we need
    to import it:

        >>> from menpowidgets.options import PatchOptionsWidget
        >>> from IPython.display import display

    Now let's define a render function that will get called on every widget
    change and will dynamically print the selected patches and bboxes flag:

        >>> from menpo.visualize import print_dynamic
        >>> def render_function(name, value):
        >>>     s = "Patches: {}, BBoxes: {}".format(
        >>>         wid.selected_values['patches']['indices'],
        >>>         wid.selected_values['bboxes']['render_lines'])
        >>>     print_dynamic(s)

    Create the widget with some initial options and display it:

        >>> patch_options = {'patches': {'command': '',
        >>>                              'indices': [],
        >>>                              'length': 68},
        >>>                  'offset_index': 0,
        >>>                  'n_offsets': 5,
        >>>                  'render_centers': True,
        >>>                  'render_patches': True,
        >>>                  'background': 'white',
        >>>                  'bboxes': {'render_lines': True,
        >>>                             'line_colour': ['r'],
        >>>                             'line_style': '-',
        >>>                             'line_width': 1}
        >>>                 }
        >>> wid = PatchOptionsWidget(patch_options,
        >>>                          render_function=render_function,
        >>>                          style='info', substyle='danger')
        >>> display(wid)

    By playing around with the widget, printed message gets updated. Finally,
    let's change the widget status with a new dictionary of options:

        >>> new_options = {'patches': {'command': '',
        >>>                            'indices': [],
        >>>                            'length':  68},
        >>>                'offset_index': 0,
        >>>                'n_offsets': 5,
        >>>                'render_centers': False,
        >>>                'render_patches': False,
        >>>                'background': 'black',
        >>>                'bboxes': {'render_lines': True,
        >>>                           'line_colour': ['r'],
        >>>                           'line_style': '-',
        >>>                           'line_width': 1}
        >>>                }
        >>> wid.set_widget_state(new_options, allow_callback=False)
    """
    def __init__(self, patch_options, render_function=None, style='minimal',
                 subwidgets_style='minimal'):
        # Create basic widgets
        offsets_dict = OrderedDict()
        for i in range(patch_options['n_offsets']):
            offsets_dict[str(i)] = i
        self.offset_dropdown = ipywidgets.Dropdown(
            options=offsets_dict, value=0, description='Offset:', width='2cm')
        self.render_centers_checkbox = ipywidgets.Checkbox(
            description='Render centres', value=patch_options['render_centers'])
        self.render_patches_checkbox = ipywidgets.Checkbox(
            description='Render patches', value=patch_options['render_patches'])

        # Create background colour toggle
        background_color, color, value = \
            self._background_args_wrt_description(patch_options['background'])
        self.background_toggle = ipywidgets.ToggleButton(
            description=patch_options['background'], color=color, value=value,
            background_color=background_color)

        def change_toggle_description(name, value):
            if value:
                self.background_toggle.description = 'white'
                self.background_toggle.background_color = '#FFFFFF'
                self.background_toggle.color = '#000000'
            else:
                self.background_toggle.description = 'black'
                self.background_toggle.background_color = '#000000'
                self.background_toggle.color = '#FFFFFF'
        self.background_toggle.on_trait_change(change_toggle_description,
                                               'value')

        self.background_title = ipywidgets.Latex(value='Background:',
                                                 margin='0.1cm')

        self.slicing_wid = SlicingCommandWidget(patch_options['patches'],
                                                description='Patches:')
        self.bboxes_line_options_wid = LineOptionsWidget(
            patch_options['bboxes'],
            render_checkbox_title='Render bounding boxes')

        # Group widgets
        self.background_box = ipywidgets.HBox(children=[
            self.background_title, self.background_toggle], align='center',
            margin='0.5cm')
        self.render_checkboxes_box = ipywidgets.Box(children=[
            self.render_patches_checkbox, self.render_centers_checkbox],
            margin='0.2cm')
        self.render_box = ipywidgets.HBox(children=[
            self.background_box, self.render_checkboxes_box], align='center')
        self.offset_patches_box = ipywidgets.VBox(
            children=[self.slicing_wid, self.offset_dropdown, self.render_box])
        super(PatchOptionsWidget, self).__init__(
            children=[self.offset_patches_box, self.bboxes_line_options_wid])
        self.align = 'start'
        self.orientation = 'horizontal'

        # Assign output
        self.selected_values = patch_options

        # Set style
        self.predefined_style(style, subwidgets_style)

        # Set functionality
        def get_background(name, value):
            bc, c, description = self._background_args_wrt_value(value)
            self.background_toggle.background_color = bc
            self.background_toggle.color = c
            self.background_toggle.description = description
            patch_options['background'] = description
        self.background_toggle.on_trait_change(get_background, 'value')

        def get_offset(name, value):
            patch_options['offset_index'] = int(value)
        self.offset_dropdown.on_trait_change(get_offset, 'value')

        def get_render_patches(name, value):
            patch_options['render_patches'] = value
        self.render_patches_checkbox.on_trait_change(get_render_patches,
                                                     'value')

        def get_render_centers(name, value):
            patch_options['render_centers'] = value
        self.render_centers_checkbox.on_trait_change(get_render_centers,
                                                     'value')

        # Set render function
        self._render_function = None
        self.add_render_function(render_function)

    def _background_args_wrt_description(self, description):
        background_color = '#FFFFFF'
        color = '#000000'
        value = True
        if description == 'black':
            background_color = '#000000'
            color = '#FFFFFF'
            value = False
        return background_color, color, value

    def _background_args_wrt_value(self, value):
        background_color = '#FFFFFF'
        color = '#000000'
        description = 'white'
        if not value:
            background_color = '#000000'
            color = '#FFFFFF'
            description = 'black'
        return background_color, color, description

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function = render_function
        if self._render_function is not None:
            self.offset_dropdown.on_trait_change(self._render_function, 'value')
            self.render_patches_checkbox.on_trait_change(self._render_function,
                                                         'value')
            self.render_centers_checkbox.on_trait_change(self._render_function,
                                                         'value')
            self.background_toggle.on_trait_change(self._render_function,
                                                   'value')
            self.slicing_wid.add_render_function(self._render_function)
            self.bboxes_line_options_wid.add_render_function(
                self._render_function)

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        self.offset_dropdown.on_trait_change(self._render_function, 'value',
                                             remove=True)
        self.render_patches_checkbox.on_trait_change(self._render_function,
                                                     'value', remove=True)
        self.render_centers_checkbox.on_trait_change(self._render_function,
                                                     'value', remove=True)
        self.background_toggle.on_trait_change(self._render_function,
                                               'value', remove=True)
        self.slicing_wid.remove_render_function()
        self.bboxes_line_options_wid.remove_render_function()
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is happening.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='dashed', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight='', bboxes_box_style=None,
              bboxes_border_visible=False, bboxes_border_color='black',
              bboxes_border_style='solid', bboxes_border_width=1,
              bboxes_border_radius=0, bboxes_padding=0, bboxes_margin=0,
              patches_box_style=None, patches_border_visible=False,
              patches_border_color='black', patches_border_style='solid',
              patches_border_width=1, patches_border_radius=0,
              patches_padding=0, patches_margin=0):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}

        bboxes_box_style : See Below, optional
            Style options for the bounding boxes

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        bboxes_border_visible : `bool`, optional
            Defines whether to draw the border line around the bounding boxes
            options.
        bboxes_border_color : `str`, optional
            The color of the border around the bounding boxes options.
        bboxes_border_style : `str`, optional
            The line style of the border around the bounding boxes options.
        bboxes_border_width : `float`, optional
            The line width of the border around the bounding boxes options.
        bboxes_border_radius : `float`, optional
            The radius of the corners of the box of the bounding boxes options.
        bboxes_padding : `float`, optional
            The padding around the bounding boxes options.
        bboxes_margin : `float`, optional
            The margin around the bounding boxes options.
        patches_box_style : See Below, optional
            Style options of the patches and offset options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        patches_border_visible : `bool`, optional
            Defines whether to draw the border line around the patches and
            offset options.
        patches_border_color : `str`, optional
            The color of the border around the patches and offset options.
        patches_border_style : `str`, optional
            The line style of the border around the patches and offset options.
        patches_border_width : `float`, optional
            The line width of the border around the patches and offset options.
        patches_border_radius : `float`, optional
            The radius of the corners of the box of the patches and offset
            options.
        patches_padding : `float`, optional
            The padding around the patches and offset options.
        patches_margin : `float`, optional
            The margin around the patches and offset options.
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.offset_dropdown, font_family, font_size, font_style,
                    font_weight)
        format_font(self.render_patches_checkbox, font_family, font_size,
                    font_style, font_weight)
        format_font(self.render_centers_checkbox, font_family, font_size,
                    font_style, font_weight)
        format_font(self.background_toggle, font_family, font_size,
                    font_style, font_weight)
        format_font(self.background_title, font_family, font_size,
                    font_style, font_weight)
        self.bboxes_line_options_wid.style(
            box_style=bboxes_box_style, border_visible=bboxes_border_visible,
            border_color=bboxes_border_color, border_style=bboxes_border_style,
            border_width=bboxes_border_width,
            border_radius=bboxes_border_radius, padding=bboxes_padding,
            margin=bboxes_margin, font_family=font_family, font_size=font_size,
            font_style=font_style, font_weight=font_weight)
        self.slicing_wid.style(
            box_style=patches_box_style, text_box_style=None,
            text_box_background_color=None, text_box_width=None, font_family='',
            font_size=None, font_style='', font_weight='')
        format_box(self.offset_patches_box, box_style=patches_box_style,
                   border_visible=patches_border_visible,
                   border_color=patches_border_color,
                   border_style=patches_border_style,
                   border_width=patches_border_width,
                   border_radius=patches_border_radius,
                   padding=patches_padding, margin=patches_margin)

    def predefined_style(self, style, subwidgets_style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Main widget (background) style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================

        subwidgets_style : `str` (see below)
            Sub-widgets (patches and bounding boxes) style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================

        """
        if style == 'minimal':
            box_style = None
            border_visible = False
            border_color = 'black'
            border_radius = 0
        elif (style == 'info' or style == 'success' or style == 'danger' or
              style == 'warning'):
            box_style = style
            border_visible = True
            border_color = map_styles_to_hex_colours(style)
            border_radius = 10
        else:
            raise ValueError('style and must be minimal or info or success '
                             'or danger or warning')

        if subwidgets_style == 'minimal':
            bboxes_box_style = None
            bboxes_border_color = 'black'
            bboxes_border_radius = 0
            patches_box_style = None
            patches_border_color = 'black'
            patches_border_radius = 0
        elif (subwidgets_style == 'info' or subwidgets_style == 'success' or
              subwidgets_style == 'danger' or subwidgets_style == 'warning'):
            bboxes_box_style = subwidgets_style
            bboxes_border_color = map_styles_to_hex_colours(subwidgets_style)
            bboxes_border_radius = 10
            patches_box_style = subwidgets_style
            patches_border_color = map_styles_to_hex_colours(subwidgets_style)
            patches_border_radius = 10
        else:
            raise ValueError('subwidgets_style and must be minimal or info '
                             'or success or danger or warning')

        self.style(
            box_style=box_style, border_visible=border_visible,
            border_color=border_color, border_style='solid', border_width=1,
            border_radius=border_radius, padding='0.2cm', margin='0.3cm',
            font_family='', font_size=None, font_style='', font_weight='',
            bboxes_box_style=bboxes_box_style, bboxes_border_visible=True,
            bboxes_border_color=bboxes_border_color,
            bboxes_border_style='solid', bboxes_border_width=1,
            bboxes_border_radius=bboxes_border_radius, bboxes_padding='0.2cm',
            bboxes_margin='0.1cm', patches_box_style=patches_box_style,
            patches_border_visible=True,
            patches_border_color=patches_border_color,
            patches_border_style='solid', patches_border_width=1,
            patches_border_radius=patches_border_radius,
            patches_padding='0.2cm', patches_margin='0.1cm')

    def set_widget_state(self, patch_options, allow_callback=True):
        r"""
        Method that updates the state of the widget with a new set of values.

        Parameters
        ----------
        patch_options : `dict`
            The dictionary with the new options to be used. For example
            ::

                patch_options = {'patches': {'command': '',
                                             'indices': [],
                                             'length': 68},
                                 'offset_index': 0,
                                 'n_offsets': 5,
                                 'render_centers': True,
                                 'render_centers': True,
                                 'background': 'white',
                                 'bboxes': {'render_lines': True,
                                            'line_colour': ['r'],
                                            'line_style': '-',
                                            'line_width': 1}
                                }

        allow_callback : `bool`, optional
            If ``True``, it allows triggering of any callback functions.
        """
        # temporarily remove render callback
        render_function = self._render_function
        self.remove_render_function()

        # Update state
        if 'n_offsets' in patch_options.keys():
            if patch_options['n_offsets'] != self.selected_values['n_offsets']:
                offsets_dict = OrderedDict()
                for i in range(patch_options['n_offsets']):
                    offsets_dict[str(i)] = i
                self.offset_dropdown.options = offsets_dict
                if self.offset_dropdown.value > patch_options['n_offsets'] - 1:
                    self.offset_dropdown.value = 0
                    self.selected_values['offset_index'] = 0
                self.selected_values['n_offsets'] = patch_options['n_offsets']

        if 'offset_index' in patch_options.keys():
            self.offset_dropdown.value = patch_options['offset_index']
            self.selected_values['offset_index'] = patch_options['offset_index']

        if 'render_patches' in patch_options.keys():
            self.render_patches_checkbox.value = patch_options['render_patches']
            self.selected_values['render_patches'] = \
                patch_options['render_patches']

        if 'render_centers' in patch_options.keys():
            self.render_centers_checkbox.value = patch_options['render_centers']
            self.selected_values['render_centers'] = \
                patch_options['render_centers']

        if 'background' in patch_options.keys():
            background_color = '#FFFFFF'
            color = '#000000'
            value = True
            if patch_options['background'] == 'black':
                background_color = '#000000'
                color = '#FFFFFF'
                value = False
            self.background_toggle.description = patch_options['background']
            self.background_toggle.color = color
            self.background_toggle.background_color = background_color
            self.background_toggle.value = value
            self.selected_values['background'] = patch_options['background']

        if 'patches' in patch_options.keys():
            self.slicing_wid.set_widget_state(patch_options['patches'],
                                              allow_callback=False)
            self.selected_values['patches'] = patch_options['patches']

        if 'bboxes' in patch_options.keys():
            self.bboxes_line_options_wid.set_widget_state(
                patch_options['bboxes'], labels=None, allow_callback=False)
            self.selected_values['bboxes'] = patch_options['bboxes']

        # Re-assign render callback
        self.add_render_function(render_function)

        # trigger render function if allowed
        if allow_callback:
            self._render_function('', True)


class LinearModelParametersWidget(ipywidgets.FlexBox):
    r"""
    Creates a widget for selecting parameters values when visualizing a linear
    model (e.g. PCA model). The widget consists of the following parts from
    `IPython.html.widgets`:

    == =========== ================== ==========================
    No Object      Variable (`self.`) Description
    == =========== ================== ==========================
    1  Button      `plot_button`      The plot variance button
    2  Button      `reset_button`     The reset button
    3  HBox        `plot_and_reset`   Contains 1, 2
                         If mode is 'single'
    ------------------------------------------------------------
    4  FloatSlider `slider`           The parameter value slider
    5  Dropdown    `dropdown_params`  The parameter selector
    6  HBox        `parameters_wid`   Contains 4, 5
                         If mode is 'multiple'
    ------------------------------------------------------------
    7  FloatSlider `sliders`          `list` of all sliders
    8  VBox        `parameters_wid`   Contains all 7
    == =========== ================== ==========================

    Note that:

    * The selected parameters are stored in the ``self.parameters`` `list`.
    * To set the styling please refer to the ``style()`` and
      ``predefined_style()`` methods.
    * To update the state of the widget, please refer to the
      ``set_widget_state()`` method.
    * To update the callback function please refer to the
      ``replace_render_function()`` and ``replace_variance_function()``
      methods.

    Parameters
    ----------
    parameters : `list`
        The `list` of initial parameters values.
    render_function : `function` or ``None``, optional
        The render function that is executed when a widgets' value changes.
        If ``None``, then nothing is assigned.
    mode : {``'single'``, ``'multiple'``}, optional
        If ``'single'``, only a single slider is constructed along with a
        dropdown menu that allows the parameter selection.
        If ``'multiple'``, a slider is constructed for each parameter.
    params_str : `str`, optional
        The string that will be used as description of the slider(s). The final
        description has the form `"{}{}".format(params_str, p)`, where `p` is
        the parameter number.
    params_bounds : (`float`, `float`), optional
        The minimum and maximum bounds, in std units, for the sliders.
    params_step : `float`, optional
        The step, in std units, of the sliders.
    plot_variance_visible : `bool`, optional
        Defines whether the button for plotting the variance will be visible
        upon construction.
    plot_variance_function : `function` or ``None``, optional
        The plot function that is executed when the plot variance button is
        clicked. If ``None``, then nothing is assigned.
    style : See Below, optional
        Sets a predefined style at the widget. Possible options are

            ========= ============================
            Style     Description
            ========= ============================
            'minimal' Simple black and white style
            'success' Green-based style
            'info'    Blue-based style
            'warning' Yellow-based style
            'danger'  Red-based style
            ''        No style
            ========= ============================

    Example
    -------
    Let's create a linear model parameters values widget and then update its
    state. Firstly, we need to import it:

        >>> from menpowidgets.options import LinearModelParametersWidget
        >>> from IPython.display import display

    Now let's define a render function that will get called on every widget
    change and will dynamically print the selected parameters:

        >>> from menpo.visualize import print_dynamic
        >>> def render_function(name, value):
        >>>     s = "Selected parameters: {}".format(wid.parameters)
        >>>     print_dynamic(s)

    Create the widget with some initial options and display it:

        >>> parameters = [-3., -2., -1., 0., 1., 2., 3.]
        >>> wid = LinearModelParametersWidget(parameters,
        >>>                                   render_function=render_function,
        >>>                                   params_str='Parameter ',
        >>>                                   mode='multiple',
        >>>                                   params_bounds=(-3., 3.),
        >>>                                   plot_variance_visible=True,
        >>>                                   style='info')
        >>> display(wid)

    By moving the sliders, the printed message gets updated. Finally, let's
    change the widget status with a new set of options:

        >>> wid.set_widget_state(parameters=[-7.] * 3, params_str='',
        >>>                      params_step=0.1, params_bounds=(-10, 10),
        >>>                      plot_variance_visible=False,
        >>>                      allow_callback=True)
    """
    def __init__(self, parameters, render_function=None, mode='multiple',
                 params_str='', params_bounds=(-3., 3.), params_step=0.1,
                 plot_variance_visible=True, plot_variance_function=None,
                 style='minimal'):
        # Check given parameters
        n_params = len(parameters)
        self._check_parameters(parameters, params_bounds)

        # If only one slider requested, then set mode to multiple
        if n_params == 1:
            mode = 'multiple'

        # Create widgets
        if mode == 'multiple':
            self.sliders = [
                ipywidgets.FloatSlider(
                    description="{}{}".format(params_str, p),
                    min=params_bounds[0], max=params_bounds[1],
                    step=params_step, value=parameters[p])
                for p in range(n_params)]
            self.parameters_wid = ipywidgets.VBox(children=self.sliders,
                                                  margin='0.2cm')
        else:
            vals = OrderedDict()
            for p in range(n_params):
                vals["{}{}".format(params_str, p)] = p
            self.slider = ipywidgets.FloatSlider(
                description='', min=params_bounds[0], max=params_bounds[1],
                step=params_step, value=parameters[0], margin='0.2cm')
            self.dropdown_params = ipywidgets.Dropdown(options=vals,
                                                       margin='0.2cm')
            self.parameters_wid = ipywidgets.HBox(
                children=[self.dropdown_params, self.slider])
        self.plot_button = ipywidgets.Button(
            description='Variance', margin='0.05cm',
            visible=plot_variance_visible)
        self.reset_button = ipywidgets.Button(description='Reset',
                                              margin='0.05cm')
        self.plot_and_reset = ipywidgets.HBox(children=[self.plot_button,
                                                        self.reset_button])

        # Widget container
        super(LinearModelParametersWidget, self).__init__(
            children=[self.parameters_wid, self.plot_and_reset])
        self.align = 'end'

        # Assign output
        self.parameters = parameters
        self.mode = mode
        self.params_str = params_str
        self.params_bounds = params_bounds
        self.params_step = params_step
        self.plot_variance_visible = plot_variance_visible

        # Set style
        self.predefined_style(style)

        # Set functionality
        if mode == 'single':
            # Assign slider value to parameters values list
            def save_slider_value(name, value):
                self.parameters[self.dropdown_params.value] = value
            self.slider.on_trait_change(save_slider_value, 'value')

            # Set correct value to slider when drop down menu value changes
            def set_slider_value(name, value):
                # Temporarily remove render callback
                render_function = self._render_function
                self.remove_render_function()
                # Set slider value
                self.slider.value = self.parameters[value]
                # Re-assign render callback
                self.add_render_function(render_function)
            self.dropdown_params.on_trait_change(set_slider_value, 'value')
        else:
            # Assign slider value to parameters values list
            def save_slider_value_from_id(description, name, value):
                i = int(description[len(params_str)::])
                self.parameters[i] = value

            # Partial function that helps get the widget's description str
            def partial_widget(description):
                return lambda name, value: save_slider_value_from_id(
                    description, name, value)

            # Assign saving values and main plotting function to all sliders
            for w in self.sliders:
                # The widget (w) is lexically scoped and so we need a way of
                # ensuring that we don't just receive the final value of w at
                # every iteration. Therefore we create another lambda function
                # that creates a new lexical scoping so that we can ensure the
                # value of w is maintained (as x) at each iteration.
                # In JavaScript, we would just use the 'let' keyword...
                w.on_trait_change(partial_widget(w.description), 'value')

        def reset_parameters(name):
            # Temporarily remove render callback
            render_function = self._render_function
            self.remove_render_function()

            # Set parameters to 0
            self.parameters = [0.0] * len(self.parameters)
            if mode == 'multiple':
                for ww in self.parameters_wid.children:
                    ww.value = 0.
            else:
                self.parameters_wid.children[0].value = 0
                self.parameters_wid.children[1].value = 0.

            # Re-assign render callback and trigger it
            self.add_render_function(render_function)
            if self._render_function is not None:
                self._render_function('', True)
        self.reset_button.on_click(reset_parameters)

        # Set plot variance function
        self._variance_function = None
        self.add_variance_function(plot_variance_function)

        # Set render function
        self._render_function = None
        self.add_render_function(render_function)

    def _check_parameters(self, parameters, bounds):
        if parameters is not None:
            for p in range(len(parameters)):
                if parameters[p] < bounds[0]:
                    parameters[p] = bounds[0]
                if parameters[p] > bounds[1]:
                    parameters[p] = bounds[1]

    def style(self, box_style=None, border_visible=False, border_color='black',
              border_style='solid', border_width=1, border_radius=0, padding=0,
              margin=0, font_family='', font_size=None, font_style='',
              font_weight='', slider_width='', slider_handle_colour=None,
              slider_background_colour=None, buttons_style=''):
        r"""
        Function that defines the styling of the widget.

        Parameters
        ----------
        box_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================

        border_visible : `bool`, optional
            Defines whether to draw the border line around the widget.
        border_color : `str`, optional
            The color of the border around the widget.
        border_style : `str`, optional
            The line style of the border around the widget.
        border_width : `float`, optional
            The line width of the border around the widget.
        border_radius : `float`, optional
            The radius of the corners of the box.
        padding : `float`, optional
            The padding around the widget.
        margin : `float`, optional
            The margin around the widget.
        font_family : See Below, optional
            The font family to be used.
            Example options ::

                {'serif', 'sans-serif', 'cursive', 'fantasy', 'monospace',
                 'helvetica'}

        font_size : `int`, optional
            The font size.
        font_style : {``'normal'``, ``'italic'``, ``'oblique'``}, optional
            The font style.
        font_weight : See Below, optional
            The font weight.
            Example options ::

                {'ultralight', 'light', 'normal', 'regular', 'book', 'medium',
                 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
                 'extra bold', 'black'}

        slider_width : `str`, optional
            The width of the slider(s).
        slider_handle_colour : `str`, optional
            The colour of the handle(s) of the slider(s).
        slider_background_colour : `str`, optional
            The background colour of the slider(s).
        buttons_style : See Below, optional
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'primary' Blue-based style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        Default style
                None      No style
                ========= ============================
        """
        format_box(self, box_style, border_visible, border_color, border_style,
                   border_width, border_radius, padding, margin)
        format_font(self, font_family, font_size, font_style, font_weight)
        format_font(self.reset_button, font_family, font_size, font_style,
                    font_weight)
        format_font(self.plot_button, font_family, font_size, font_style,
                    font_weight)
        if self.mode == 'single':
            self.slider.width = slider_width
            self.slider.slider_color = slider_handle_colour
            self.slider.background_color = slider_background_colour
            format_font(self.slider, font_family, font_size, font_style,
                        font_weight)
            format_font(self.dropdown_params, font_family, font_size,
                        font_style, font_weight)
        else:
            for sl in self.sliders:
                sl.width = slider_width
                sl.slider_color = slider_handle_colour
                sl.background_color = slider_background_colour
                format_font(sl, font_family, font_size, font_style,
                            font_weight)
        self.reset_button.button_style = buttons_style
        self.plot_button.button_style = buttons_style

    def predefined_style(self, style):
        r"""
        Function that sets a predefined style on the widget.

        Parameters
        ----------
        style : `str` (see below)
            Style options

                ========= ============================
                Style     Description
                ========= ============================
                'minimal' Simple black and white style
                'success' Green-based style
                'info'    Blue-based style
                'warning' Yellow-based style
                'danger'  Red-based style
                ''        No style
                ========= ============================
        """
        if style == 'minimal':
            self.style(box_style=None, border_visible=True,
                       border_color='black', border_style='solid',
                       border_width=1, border_radius=0, padding='0.2cm',
                       margin='0.3cm', font_family='', font_size=None,
                       font_style='', font_weight='', slider_width='',
                       slider_handle_colour=None,
                       slider_background_colour=None, buttons_style='')
        elif (style == 'info' or style == 'success' or style == 'danger' or
                      style == 'warning'):
            self.style(box_style=style, border_visible=True,
                       border_color=map_styles_to_hex_colours(style),
                       border_style='solid', border_width=1, border_radius=10,
                       padding='0.2cm', margin='0.3cm', font_family='',
                       font_size=None, font_style='', font_weight='',
                       slider_width='',
                       slider_handle_colour=map_styles_to_hex_colours(style),
                       slider_background_colour=None,
                       buttons_style='primary')
        else:
            raise ValueError('style must be minimal or info or success or '
                             'danger or warning')

    def add_render_function(self, render_function):
        r"""
        Method that adds a `render_function()` to the widget. The signature of
        the given function is also stored in `self._render_function`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing is added.
        """
        self._render_function = render_function
        if self._render_function is not None:
            if self.mode == 'single':
                self.slider.on_trait_change(self._render_function, 'value')
            else:
                for sl in self.sliders:
                    sl.on_trait_change(self._render_function, 'value')

    def remove_render_function(self):
        r"""
        Method that removes the current `self._render_function()` from the
        widget and sets ``self._render_function = None``.
        """
        if self.mode == 'single':
            self.slider.on_trait_change(self._render_function, 'value',
                                        remove=True)
        else:
            for sl in self.sliders:
                sl.on_trait_change(self._render_function, 'value', remove=True)
        self._render_function = None

    def replace_render_function(self, render_function):
        r"""
        Method that replaces the current `self._render_function()` of the widget
        with the given `render_function()`.

        Parameters
        ----------
        render_function : `function` or ``None``, optional
            The render function that behaves as a callback. If ``None``, then
            nothing happens.
        """
        # remove old function
        self.remove_render_function()

        # add new function
        self.add_render_function(render_function)

    def add_variance_function(self, variance_function):
        r"""
        Method that adds a `variance_function()` to the `Variance` button of the
        widget. The signature of the given function is also stored in
        `self._variance_function`.

        Parameters
        ----------
        variance_function : `function` or ``None``, optional
            The variance function that behaves as a callback. If ``None``,
            then nothing is added.
        """
        self._variance_function = variance_function
        if self._variance_function is not None:
            self.plot_button.on_click(self._variance_function)

    def remove_variance_function(self):
        r"""
        Method that removes the current `self._variance_function()` from
        the `Variance` button of the widget and sets
        ``self._variance_function = None``.
        """
        self.plot_button.on_click(self._variance_function, remove=True)
        self._variance_function = None

    def replace_variance_function(self, variance_function):
        r"""
        Method that replaces the current `self._variance_function()` of the
        `Variance` button of the widget with the given `variance_function()`.

        Parameters
        ----------
        variance_function : `function` or ``None``, optional
            The variance function that behaves as a callback. If ``None``,
            then nothing happens.
        """
        # remove old function
        self.remove_variance_function()

        # add new function
        self.add_variance_function(variance_function)

    def set_widget_state(self, parameters=None, params_str=None,
                         params_bounds=None, params_step=None,
                         plot_variance_visible=True, allow_callback=True):
        r"""
        Method that updates the state of the widget with a new set of options.

        Parameters
        ----------
        parameters : `list` or ``None``, optional
            The `list` of new parameters' values. If ``None``, then nothing
            changes.
        params_str : `str` or ``None``, optional
            The string that will be used as description of the slider(s). The
            final description has the form `"{}{}".format(params_str, p)`, where
            `p` is the parameter number. If ``None``, then nothing changes.
        params_bounds : (`float`, `float`) or ``None``, optional
            The minimum and maximum bounds, in std units, for the sliders. If
            ``None``, then nothing changes.
        params_step : `float` or ``None``, optional
            The step, in std units, of the sliders. If ``None``, then nothing
            changes.
        plot_variance_visible : `bool`, optional
            Defines whether the button for plotting the variance will be
            visible.
        allow_callback : `bool`, optional
            If ``True``, it allows triggering of any callback functions.
        """
        # Temporarily remove render callback
        render_function = self._render_function
        self.remove_render_function()

        # Parse given options
        if parameters is None:
            parameters = self.parameters
        if params_str is None:
            params_str = ''
        if params_bounds is None:
            params_bounds = self.params_bounds
        if params_step is None:
            params_step = self.params_step

        # Check given parameters
        self._check_parameters(parameters, params_bounds)

        # Set plot variance visibility
        self.plot_button.visible = plot_variance_visible

        # Update widget
        if len(parameters) == len(self.parameters):
            # The number of parameters hasn't changed
            if self.mode == 'multiple':
                for p, sl in enumerate(self.sliders):
                    sl.value = parameters[p]
                    sl.description = "{}{}".format(params_str, p)
                    sl.min = params_bounds[0]
                    sl.max = params_bounds[1]
                    sl.step = params_step
            else:
                self.slider.min = params_bounds[0]
                self.slider.max = params_bounds[1]
                self.slider.step = params_step
                if not params_str == '':
                    vals = OrderedDict()
                    for p in range(len(parameters)):
                        vals["{}{}".format(params_str, p)] = p
                    self.dropdown_params.options = vals
                self.slider.value = parameters[self.dropdown_params.value]
        else:
            # The number of parameters has changed
            if self.mode == 'multiple':
                # Create new sliders
                self.sliders = [
                    ipywidgets.FloatSlider(
                        description="{}{}".format(params_str, p),
                        min=params_bounds[0], max=params_bounds[1],
                        step=params_step, value=parameters[p])
                    for p in range(len(parameters))]
                # Set sliders as the children of the container
                self.parameters_wid.children = self.sliders

                # Assign slider value to parameters values list
                def save_slider_value_from_id(description, name, value):
                    i = int(description[len(params_str)::])
                    self.parameters[i] = value

                # Partial function that helps get the widget's description str
                def partial_widget(description):
                    return lambda name, value: save_slider_value_from_id(
                        description, name, value)

                # Assign saving values and main plotting function to all sliders
                for w in self.sliders:
                    # The widget (w) is lexically scoped and so we need a way of
                    # ensuring that we don't just receive the final value of w
                    # at every iteration. Therefore we create another lambda
                    # function that creates a new lexical scoping so that we can
                    # ensure the value of w is maintained (as x) at each
                    # iteration. In JavaScript, we would just use the 'let'
                    # keyword...
                    w.on_trait_change(partial_widget(w.description), 'value')

                # Set style
                if self.box_style is None:
                    self.predefined_style('minimal')
                else:
                    self.predefined_style(self.box_style)
            else:
                self.slider.min = params_bounds[0]
                self.slider.max = params_bounds[1]
                self.slider.step = params_step
                vals = OrderedDict()
                for p in range(len(parameters)):
                    vals["{}{}".format(params_str, p)] = p
                if self.dropdown_params.value == 0:
                    self.dropdown_params.value = 1
                    self.dropdown_params.value = 0
                else:
                    self.dropdown_params.value = 0
                self.dropdown_params.options = vals
                self.slider.value = parameters[0]

        # Re-assign render callback
        self.add_render_function(render_function)

        # Assign new selected options
        self.parameters = parameters
        self.params_str = params_str
        self.params_bounds = params_bounds
        self.params_step = params_step
        self.plot_variance_visible = plot_variance_visible

        # trigger render function if allowed
        if allow_callback:
            self._render_function('', True)
