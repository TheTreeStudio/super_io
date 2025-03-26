import bpy
from ..ops.core import get_pref
from ..preferences.prefs import SPIO_Preference
from ..preferences.data_icon import G_ICON_ID

_panels_registered = False # 新增全局变量，用于跟踪面板是否已注册

class SidebarSetup:
    bl_category = "SPIO"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    # bl_options = {'DRAW_BOX'}

    @classmethod
    def poll(cls, context):
        return True


class SPIO_PT_PrefPanel(SidebarSetup, bpy.types.Panel):
    bl_label = ''

    def draw_header(self, context):
        layout = self.layout
        layout.alignment = "LEFT"
        pref = get_pref()

        row = layout
        row = row.row(align=True)
        row.prop(pref, 'ui', expand=True, emboss=False)
        row.separator()
        row.menu('SPIO_MT_ConfigIOMenu', text='', icon='FILE_TICK')
        row.separator(factor=2)

    def draw(self, context):
        layout = self.layout
        pref = get_pref()
        if pref.ui == 'SETTINGS':
            SPIO_Preference.draw_settings(pref, context, layout)
        elif pref.ui == 'CONFIG':
            SPIO_Preference.draw_config(pref, context, layout)


class SPIO_PT_PrefPanel_283(SPIO_PT_PrefPanel):
    bl_label = ' '
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return super().poll(context) and bpy.app.version < (3, 0, 0)


class SPIO_PT_PrefPanel_300(SPIO_PT_PrefPanel):
    bl_options = {'HEADER_LAYOUT_EXPAND', 'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return super().poll(context) and not bpy.app.version < (3, 0, 0)


class SPIO_PT_ImportPanel(SidebarSetup, bpy.types.Panel):
    bl_label = 'Super IO'

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'CENTER'
        row.scale_y = 1.5
        row.separator()
        row.operator("wm.super_import", icon_value=G_ICON_ID['import'])
        row.operator("wm.super_export", icon_value=G_ICON_ID['export'])
        row.separator()


class SPIO_PT_AssetHelper(SidebarSetup, bpy.types.Panel):
    bl_label = 'Asset Helper'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return get_pref().asset_helper and bpy.app.version >= (3, 0, 0)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        subbox = layout.box()
        subbox.label(text='Active Asset Preview', icon='IMAGE_DATA')
        row = subbox.box().row()
        row.alignment = 'LEFT'
        row.label(text='Active Object')
        row.label(text=context.object.name if context.object else 'No Active Object',
                  icon='OBJECT_DATA' if context.object else 'ERROR')

        col = subbox.column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(context.scene, 'spio_snapshot_resolution', slider=True)
        col.prop(context.scene, 'spio_snapshot_view', slider=True)
        col.prop(context.scene, 'spio_snapshot_render_settings', slider=True)
        subbox.operator('spio.asset_snap_shot', icon='RENDER_STILL')

        # box.operator('spio.render_hdri_preview', icon='WORLD')
        # box.operator('spio.set_asset_thumb_from_clipboard_image', icon='IMPORT')


panels = [
    SPIO_PT_PrefPanel_283,
    SPIO_PT_PrefPanel_300,
    SPIO_PT_ImportPanel,
    SPIO_PT_AssetHelper,
]


def register():
    global _panels_registered
    if _panels_registered:
        return
        
    try:
        pref = get_pref()
        if not pref.show_n_panel:
            return

        # 根据版本选择需要注册的面板
        version_panel = (
            SPIO_PT_PrefPanel_283 
            if bpy.app.version < (3, 0, 0) 
            else SPIO_PT_PrefPanel_300
        )
        
        # 注册核心面板
        panels_to_register = [
            version_panel,
            SPIO_PT_ImportPanel,
            SPIO_PT_AssetHelper
        ]
        
        for panel in panels_to_register:
            try:
                if not hasattr(bpy.types, panel.__name__):
                    bpy.utils.register_class(panel)
            except Exception as e:
                print(f"Error registering {panel.__name__}: {e}")

        _panels_registered = True
    except Exception as e:
        print(f"Registration failed: {e}")

def unregister():
    global _panels_registered
    if _panels_registered:
        # 根据当前Blender版本选择需要注销的面板
        version_specific_panels = [
            SPIO_PT_PrefPanel_283 if bpy.app.version < (3, 0, 0) 
            else SPIO_PT_PrefPanel_300,
            SPIO_PT_ImportPanel,
            SPIO_PT_AssetHelper
        ]
        
        # 仅注销当前版本实际注册的面板
        for panel in version_specific_panels:
            if hasattr(bpy.types, panel.__name__):
                try:
                    bpy.utils.unregister_class(panel)
                except Exception as e:
                    print(f"Error unregistering {panel.__name__}: {e}")
        
        _panels_registered = False

def update_panel_visibility():
    """更安全的面板更新逻辑"""
    try:
        # 强制重置注册状态
        global _panels_registered
        if _panels_registered:
            unregister()
        
        # 获取最新首选项设置
        pref = get_pref()
        if pref.show_n_panel:
            register()
    except Exception as e:
        print(f"Panel visibility update failed: {e}")