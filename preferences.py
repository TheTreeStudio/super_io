import bpy
import os
from bpy.props import (EnumProperty,
                       StringProperty,
                       BoolProperty,
                       CollectionProperty,
                       IntProperty,
                       FloatProperty,
                       PointerProperty)
from bpy.types import PropertyGroup

from . import __folder_name__


def get_pref():
    """get preferences of this plugin"""
    return bpy.context.preferences.addons.get(__folder_name__).preferences


class OperatorProperty(PropertyGroup):
    name: StringProperty(name='Property')
    value: StringProperty(name='Value')


def correct_blidname(self, context):
    if self.bl_idname.startswith('bpy.ops.'):
        self.bl_idname = self.bl_idname[8:]
    if self.bl_idname.endswith('()'):
        self.bl_idname = self.bl_idname[:-2]


def correct_name(self, context):
    pref = get_pref()
    names = [item.name for item in pref.config_list if item.name == self.name and item.name != '']
    if len(names) != 1:
        self.name += '(1)'


class ExtensionOperatorProperty(PropertyGroup):
    # UI
    expand_panel: BoolProperty(name='Expand Panel', default=True)
    # USE
    use_config: BoolProperty(name='Use', default=True)

    name: StringProperty(name='Preset Name', update=correct_name)
    extension: StringProperty(name='Extension')
    bl_idname: StringProperty(name='Operator Identifier', update=correct_blidname)
    prop_list: CollectionProperty(type=OperatorProperty)


class OperatorPropAction:
    bl_label = "Operator Props Operate"
    bl_options = {'REGISTER', 'UNDO'}

    config_list_index: IntProperty()
    prop_index: IntProperty()
    action = None

    def execute(self, context):
        pref = get_pref()
        item = pref.config_list[self.config_list_index]

        if self.action == 'ADD':
            item.prop_list.add()
        elif self.action == 'REMOVE':
            item.prop_list.remove(self.prop_index)

        return {'FINISHED'}


class SPIO_OT_OperatorPropAdd(OperatorPropAction, bpy.types.Operator):
    bl_idname = "wm.spio_operator_prop_add"
    bl_label = "Add Prop"

    action = 'ADD'


class SPIO_OT_OperatorPropRemove(OperatorPropAction, bpy.types.Operator):
    bl_idname = "wm.spio_operator_prop_remove"
    bl_label = "Remove Prop"

    action = 'REMOVE'


class SPIO_OT_ExtensionListAction:
    """Add / Remove / Copy current config"""
    bl_label = "Config Operate"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()
    action = None

    def execute(self, context):
        pref = get_pref()

        if self.action == 'ADD':
            item = pref.config_list.add()
            item.name = f'Config{len(pref.config_list)}'
            pref.config_list_index = len(pref.config_list) - 1

        elif self.action == 'REMOVE':
            pref.config_list.remove(self.index)
            pref.config_list_index = self.index - 1 if self.index != 0 else 0

        elif self.action == 'COPY':
            cur_item = pref.config_list[self.index]

            item = pref.config_list.add()
            item.name = cur_item.name + '_copy'
            item.use_config = cur_item.use_config
            item.extension = cur_item.extension
            item.bl_idname = cur_item.bl_idname

            for cur_prop_item in cur_item.prop_list:
                prop_item = item.prop_list.add()
                prop_item.name = cur_prop_item.name
                prop_item.value = cur_prop_item.value

            pref.config_list_index = len(pref.config_list) - 1

        return {'FINISHED'}


class SPIO_OT_ExtensionListAdd(SPIO_OT_ExtensionListAction,bpy.types.Operator):
    bl_idname = "wm.spio_config_list_add"
    bl_label = "Add Config"

    action = 'ADD'


class SPIO_OT_ExtensionListRemove(SPIO_OT_ExtensionListAction,bpy.types.Operator):
    bl_idname = "wm.spio_config_list_remove"
    bl_label = "Remove Config"

    action = 'REMOVE'


class SPIO_OT_ExtensionListCopy(SPIO_OT_ExtensionListAction,bpy.types.Operator):
    bl_idname = "wm.spio_config_list_copy"
    bl_label = "Copy Config"

    action = 'COPY'


class PREF_UL_ConfigList(bpy.types.UIList):
    filter_type: EnumProperty(name='Filter Type', items=[
        ('NAME', 'Name', ''),
        ('EXT', 'Extension', ''),
    ])

    filter_extension: StringProperty(
        default='',
        name="Filter Extension")

    reverse: BoolProperty(
        name="Reverse",
        default=False,
        options=set(),
        description="Reverse current filtering",
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.5)
        sub = row.row(align=1)
        sub.prop(item, 'use_config', text='')
        sub.prop(item, 'name', text='', emboss=False)
        sub.prop(item, 'extension', text='', emboss=False)
        row.prop(item, 'bl_idname', text='', emboss=False)

    def draw_filter(self, context, layout):
        """UI code for the filtering/sorting/search area."""
        layout.separator()
        col = layout.column()

        col.prop(self, 'filter_type', icon='FILTER')

        row = col.row(align=1)
        if self.filter_type == 'EXT':
            row.prop(self, 'filter_extension', text='Extension')
        else:
            row.prop(self, "filter_name", text="Name")

        row.prop(self, "reverse", text="", icon='ARROW_LEFTRIGHT')

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        ordered = []
        filtered = [self.bitflag_filter_item] * len(items)

        if self.filter_type == 'EXT':
            for i, item in enumerate(items):
                if item.extension != self.filter_extension and self.filter_extension != '':
                    filtered[i] &= ~self.bitflag_filter_item

        else:
            if self.filter_name:
                filtered = bpy.types.UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, items,
                                                                     "name", reverse=self.reverse)
        # invert
        if filtered and self.reverse:
            show_flag = self.bitflag_filter_item & ~self.bitflag_filter_item
            for i, bitflag in enumerate(filtered):
                if bitflag == show_flag:
                    filtered[i] = self.bitflag_filter_item
                else:
                    filtered[i] &= ~self.bitflag_filter_item

        if self.filter_type == 'EXT':
            try:
                ordered = bpy.types.UI_UL_list.sort_items_helper(items, lambda i: len(i.extension), True)
            except:
                pass
        else:
            try:
                ordered = bpy.types.UI_UL_list.sort_items_helper(items, 'name')
            except:
                pass
        return filtered, ordered


class SPIO_Preference(bpy.types.AddonPreferences):
    bl_idname = __package__

    # UI
    ui: EnumProperty(items=[
        ('SETTINGS', 'Settings', '', 'PREFERENCES', 0),
        ('CONFIG', 'Config', '', 'PRESET', 1),
    ])
    # Settings
    force_unicode: BoolProperty(name='Force Unicode',
                                description='Force to use "utf-8" to decode filepath \n'
                                            'Only enable when your system coding "utf-8"')
    report_time: BoolProperty(name='Report time', description='Report import time', default=True)
    # Preset
    config_list: CollectionProperty(type=ExtensionOperatorProperty)
    config_list_index: IntProperty(min=0, default=0)

    def draw(self, context):
        layout = self.layout.split(factor=0.2)
        layout.scale_y = 1.2

        col = layout.column(align=True)
        col.prop(self, 'ui', expand=True)

        col.separator(factor=2)
        self.draw_import(context, col)

        col = layout.column()
        if self.ui == 'SETTINGS':
            self.draw_settings(context, col)
        elif self.ui == 'CONFIG':
            self.draw_config(context, col)

    def draw_import(self, context, layout):
        layout.operator('spio.config_import', icon='IMPORT')
        layout.operator('spio.config_export', icon='EXPORT')

    def draw_settings(self, context, layout):
        layout.use_property_split = True
        layout.prop(self, 'force_unicode')
        layout.prop(self, 'report_time')

    def draw_config(self, context, layout):
        row = layout.column(align=True).row()

        row_left = row

        row_l = row_left.row(align=True)
        col_list = row_l.column(align=True)
        col_btn = row_l.column(align=True)

        col_list.template_list(
            "PREF_UL_ConfigList", "Config List",
            self, "config_list",
            self, "config_list_index")

        col_btn.operator('wm.spio_config_list_add', text='', icon='ADD')

        d = col_btn.operator('wm.spio_config_list_remove', text='', icon='REMOVE')
        d.index = self.config_list_index

        c = col_btn.operator('wm.spio_config_list_copy', text='', icon='DUPLICATE')
        c.index = self.config_list_index

        if len(self.config_list) == 0: return
        item = self.config_list[self.config_list_index]
        if not item: return

        col = layout.column()
        box = col.box().column()
        box.label(text=item.name, icon='EDITMODE_HLT')

        box.use_property_split = True
        box.prop(item, 'name')
        box.prop(item, 'extension')
        box.prop(item, 'bl_idname')

        # ops props
        col = box.box().column()

        row = col.row(align=True)
        if item.bl_idname != '':
            text = 'bpy.ops.' + item.bl_idname + '(' + 'filepath,' + '{prop=value})'
        else:
            text = 'No Operator Found'

        row.label(icon='TOOL_SETTINGS', text=text)


        if item.bl_idname != '':
            row = col.row()
            if len(item.prop_list) != 0:
                row.label(text = 'Property')
                row.label(text = 'Value')
            for prop_index, prop_item in enumerate(item.prop_list):
                row = col.row(align=True)
                row.prop(prop_item, 'name',text ='')
                row.prop(prop_item, 'value',text ='')

                d = row.operator('wm.spio_operator_prop_remove', text='', icon='PANEL_CLOSE', emboss=False)
                d.config_list_index = self.config_list_index
                d.prop_index = prop_index

                if prop_item.name != '' and prop_item.value != '':
                    text.append(f'{prop_item.name}={prop_item.value}')

        row = col.row(align=True)
        row.alignment = 'LEFT'
        d = row.operator('wm.spio_operator_prop_add', text='Add Property', icon='ADD', emboss=False)
        d.config_list_index = self.config_list_index


classes = [
    OperatorProperty,
    SPIO_OT_OperatorPropAdd, SPIO_OT_OperatorPropRemove,

    ExtensionOperatorProperty,
    SPIO_OT_ExtensionListAdd, SPIO_OT_ExtensionListRemove, SPIO_OT_ExtensionListCopy,

    PREF_UL_ConfigList,
    SPIO_Preference
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
