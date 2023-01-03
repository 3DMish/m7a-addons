#!/usr/bin/env python -------------------------------- -*- coding: utf-8 -*-#

# -----              ##### BEGIN GPL LICENSE BLOCK #####              ----- #
#                                                                           #
#  This  program  is  free  software;   you  can  redistribute  it  and/or  #
#  modify  it  under  the  terms  of   the   GNU  General  Public  License  #
#  as  published  by  the  Free  Software  Foundation;  either  version  2  #
#  of the License, or (at your option) any later version.                   #
#                                                                           #
#  This program  is  distributed  in the hope  that  it  will  be  useful,  #
#  but  WITHOUT  ANY  WARRANTY;  without  even  the  implied  warranty  of  #
#  MERCHANTABILITY  or  FITNESS   FOR  A  PARTICULAR  PURPOSE.    See  the  #
#  GNU General Public License for more details.                             #
#                                                                           #
#  You  should  have  received  a  copy  of the GNU General Public License  #
#  along with this program; if not, write to the Free Software Foundation,  #
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.       #
#                                                                           #
# -----               ##### END GPL LICENSE BLOCK #####               ----- #

import bpy, sys, os, math, bmesh, time, inspect, mathutils, subprocess;
import bpy.utils.previews;

from bpy.types import Panel as panel, Operator as operator, PropertyGroup as prop_group;
from bpy.types import UIList as ui_list;
from bpy.app import version as bpy_version;

bpy_u80 = True if  (2, 79, 0) < bpy_version  else False;
bpy_d80 = True if  (2, 80, 0) > bpy_version  else False;
bpy_u90 = True if  (2, 89, 0) < bpy_version  else False;
bpy_u93 = True if  (2, 93, 0) < bpy_version  else False;
bpy_u3  = True if  (3, 0, 0) <= bpy_version  else False;

bpy_s90 = True if ((2, 90, 0) > bpy_version) and ((2, 79, 0) < bpy_version) else False;

def scene(): return bpy.context.scene;

from mathutils.geometry import delaunay_2d_cdt;

from bpy.props import IntProperty   as int_prop,   StringProperty      as str_prop;
from bpy.props import BoolProperty  as bool_prop,  PointerProperty     as point_prop;
from bpy.props import EnumProperty  as enum_prop,  CollectionProperty  as collect_prop;
from bpy.props import FloatProperty as float_prop, FloatVectorProperty as float_v_prop;

bl_info = {
    "name":        "Morphing Images v2.0",
    "category":    "3DMish",
    "author":      "3DMish (Mish7913)",
    "version":     (2, 0, 0),
    "blender":     (3, 0, 0),
    "wiki_url":    "https://3dmish.blogspot.com/p/3dm-morph-en.html",
    "tracker_url": "",
    "description": "Morphing images",
}

bl_conf = {
    "panel": "main",
}

morph_list_opts = [
    ("point_center", "Add point in Center Image",    "Add new point in center image"),
    ("3d_cursor",    "Add point on 3D Cursor",       "Add new point in center 3d cursor"),
    #("view_center",  "Add point in ViewPort center", "Add new point in center of viewport"),
];

morph_list_form = [
    ("dot",      "Dot",      "Add new point as dot",      "DOT"              if bpy_u80 else "LAYER_ACTIVE", 0),
    ("square",   "Square",   "Add new point as square",   "MESH_PLANE",                                      1),
    ("circle",   "Circle",   "Add new point as circle",   "MESH_CIRCLE",                                     2),
    ("rhombus",  "Rhombus",  "Add new point as rhombus",  "DECORATE_ANIMATE" if bpy_u80 else "SPACE3",       3),
    ("tracker",  "Tracker",  "Add new point as tracker",  "TRACKER"          if bpy_u80 else "CURSOR",       4),
    ("triangle", "Triangle", "Add new point as triangle", "MESH_CONE",                                       5),
    ("star",     "Star",     "Add new point as star",     "SOLO_OFF",                                        6),
];

morph_list_Method = [
    ("sub", "Subdivision (OLD)", "Method Subdivision Surface", "MOD_SUBSURF", 0),
    ("del", "Delaunay", "Method Delaunay", "MESH_DATA", 1),
];

morph_list_animate_by = [
    ("auto", "Animate by: Auto", "Method Connections Auto", "ARMATURE_AUTO", 0),
    ("envl", "Animate by: Envelope", "Method Connections Envelope", "ARMATURE_ENVELOPE", 1),
];

def a_obj(): return bpy.context.active_object;
def s_obj(): return bpy.context.selected_objects;
def get_obj(name): return bpy.data.objects[name];

morph_armature = None;
morph_list_morphs = {};

class mish_morph:
    bl_category    = "3DMish";
    bl_label       = "M7A Morphing Images v2.0";
    bl_space_type  = "VIEW_3D";
    bl_region_type = "TOOLS" if bpy_d80 else "UI";

class m7a_morph_panel(mish_morph, panel):
    bl_idname = "m7a_morph_main_panel";

    def draw(self, context):
        global bl_conf; morph_l = scene().m7a_morph_l;
        lc_main = self.layout.column(align = False);
        ic_morph = False;
        
        try:
            if (bpy.context.active_object.get("mish_morph") != None): bl_conf["panel"] = "start";
            else: bl_conf["panel"] = "main";
        except: bl_conf["panel"] = "main";
            
        if (bl_conf["panel"] == "main") or (bpy.context.active_object.type != "ARMATURE"):
            ic_edit = False;
            try: 
                if (bpy.context.active_object.get("mish_main_morph") != None):
                    ic_edit = True;
            except: pass
            
            if (ic_edit == False):
                lc_row = lc_main.row(align = True);
                lc_row.label(text="M7A Morphing Images");
                lc_row.label(text="", icon="RENDER_RESULT" if bpy_u80 else "IMAGE_COL");
                lc_row = lc_main.row(align = True);
                lc_row.prop(scene(), "m7a_morph_ratio", text="", icon="OBJECT_DATAMODE", toggle=True);
                lc_row.prop(scene(), "m7a_morph_x");
                lc_row.prop(scene(), "m7a_morph_y");
                lc_row.operator("3dmish.moprh_aspect_ratio", icon="AXIS_SIDE" if bpy_u80 else "AXIS_TOP", text="");
                lc_list = lc_main.column(align = True);
                lc_list.template_list("m7a_morph_items", "list_images", morph_l, "list", morph_l, "active", rows=5);
                lc_list_btns = lc_list.row(align = True);
                lc_list_btns.operator('3dmish.moprh_add_image',    icon='ADD'    if bpy_u80 else "ZOOMIN",  text="");
                lc_list_btns.operator('3dmish.moprh_remove_image', icon='REMOVE' if bpy_u80 else "ZOOMOUT", text="");
                lc_row = lc_list_btns.row(align = True);
                lc_row.alignment = "CENTER";
                lc_row.label(text=str(len(morph_l.list)));
                lc_list_btns.operator('3dmish.morph_move_up_image',   icon='TRIA_UP',   text="");
                lc_list_btns.operator('3dmish.morph_move_down_image', icon='TRIA_DOWN', text="");
                lc_main.separator();
                lc_main.operator('3dmish.morph_start', icon='FILE_NEW' if bpy_u80 else 'NEW', text="Start Morph");
            else:
                lc_row = lc_main.row(align = True);
                lc_row.operator('3dmish.morph_cancel', icon='BACK', text='Cancel');
                lc_row.label(text="New Morph");
                lc_row.label(text="", icon='FILE_NEW' if bpy_u80 else 'NEW');
                lc_main.separator();
                lc_main.operator('3dmish.morph_edit', icon='OUTLINER_DATA_MESH', text='Edit Morph');
                lc_main.separator();
        elif (bl_conf["panel"] == "start") and (bpy.context.active_object.type == "ARMATURE") and (bpy.context.object.mode == "POSE"):
            lc_row = lc_main.row(align = True);
            lc_row.operator('3dmish.morph_cancel', icon='BACK', text='Cancel');
            lc_row.label(text="New Morph");
            lc_row.label(text="", icon='FILE_NEW' if bpy_u80 else 'NEW');
            lc_main.separator();
            lc_main.prop(scene(), 'm7a_morph_opts', text="", icon='OUTLINER' if bpy_u80 else "OOPS");
            lc_col = lc_main.column(align = True);
            lc_row = lc_col.row(align = True);
            lc_btn_1 = lc_button(lc_row, '3dmish.morph_add_point', "Add Point", 'ADD' if bpy_u80 else "ZOOMIN");
            if (bpy.context.object.mode == "POSE"): lc_btn_1.enable();
            else: lc_btn_1.disable();
            lc_btn_2 = lc_button(lc_row, '3dmish.morph_remove_point', "", 'REMOVE' if bpy_u80 else "ZOOMOUT");
            if (bpy.context.object.mode == "POSE"): lc_btn_2.enable();
            else: lc_btn_2.disable();
            lc_row = lc_col.row(align = True);
            #lc_btn_1 = lc_button(lc_row, '3dmish.morph_create_line', "Create Line", 'ADD' if bpy_u80 else "ZOOMIN");
            if (bpy.context.object.mode == "POSE"): lc_btn_1.enable();
            else: lc_btn_1.disable();
            #lc_btn_2 = lc_button(lc_row, '3dmish.morph_remove_line', "", 'REMOVE' if bpy_u80 else "ZOOMOUT");
            if (bpy.context.object.mode == "POSE"): lc_btn_2.enable();
            else: lc_btn_2.disable();
            lc_row = lc_main.row(align = True);
            lc_row.operator('3dmish.morph_show_selected', icon='CON_OBJECTSOLVER');
            
            btn = lc_row.operator('mish_morph.btn', text="", icon='TRACKING_BACKWARDS_SINGLE');
            btn.bl_desc = "Jump to previous point"; btn.bl_btn = "jump_to_point"; btn.bl_opt = "-1";
            
            btn = lc_row.operator('mish_morph.btn', text="", icon='TRACKING_FORWARDS_SINGLE');
            btn.bl_desc = "Jump to next point"; btn.bl_btn = "jump_to_point"; btn.bl_opt = "1";
            
            lc_main.prop(scene(), 'm7a_morph_form', text="Form");
            lc_main.prop(scene(), 'm7a_morph_point_size', text="Point Size");
            
            lc_row = lc_main.row(align = True);
            lc_btns = lc_row.row(align = True);
            if (scene().m7a_morph_method == "sub"):
                lc_btns.prop(scene(), 'm7a_morph_subdevision', text="Sub");
            else:
                lc_btns.prop(scene(), 'm7a_morph_quality', text="Quality");
            lc_btns.enabled = True if (scene().m7a_morph_method == "sub") else False;
            lc_row.prop(scene(), 'm7a_morph_borders', text="Fixed Borders", toggle=True);
            lc_main.prop(scene(), 'm7a_morph_method', text="Method");
            #lc_col = lc_main.column(align = True);
            #lc_col.operator('3dmish.morph_preview', icon='SCENE' if bpy_u80 else "ZOOM_SELECTED");
            #lc_prew = lc_col.column(align = True);
            #lc_prew.prop(scene(), 'm7a_morph_preview', text="Preview slider");
            #lc_prew.active = False;
            lc_main.separator();
            lc_main.operator('3dmish.morph_create', icon='RENDER_RESULT' if bpy_u80 else "IMAGE_COL");
        else:
            lc_row = lc_main.row(align = True);
            if (bpy.context.active_object.get("mish_morph") != None):
                lc_row.operator('3dmish.morph_cancel', icon='BACK', text='Cancel');
                lc_row.label(text="New Morph");
                lc_row.label(text="", icon='FILE_NEW' if bpy_u80 else 'NEW');
                lc_main.separator();
                lc_main.operator('3dmish.morph_edit', icon='OUTLINER_DATA_MESH', text='Edit Morph');
            else:
                lc_row.operator('3dmish.morph_main', icon='BACK', text='Back');
            lc_main.separator();
 
class m7a_morph_settings(mish_morph, panel):
    bl_parent_id = "m7a_morph_main_panel";
    bl_idname = "m7a_morph_settings";
    bl_label = "Settings";
    bl_options = {'DEFAULT_CLOSED'};
     
    @classmethod
    def poll(cls, context):
        global bl_conf;
        if (bl_conf["panel"] == "start") and (bpy.context.object.mode == "POSE"): return True;
        else: return False;
    
    def draw(self, context):
        global bl_conf;
        lc_main = self.layout.column(align = False);
        lc_main.prop(scene(), 'm7a_morph_animate_by', text="");
        if (scene().m7a_morph_animate_by == "envl"):
            lc_main.prop(scene(), 'm7a_morph_envelope', text="Envelope Distance");
        lc_main.prop(scene(), 'm7a_morph_transparent', text="Transparent Background (Beta)");
        lc_main.prop(scene(), 'm7a_morph_use_vrtx', text="Use Image Vertex");
        lc_main.prop(scene(), 'm7a_morph_loop', text="Loop");

class m7a_morph_settings_change(mish_morph, panel):
    bl_parent_id = "m7a_morph_settings";
    bl_idname = "m7a_morph_settings_change";
    bl_label = "Change Point(s)";
    
    def draw(self, context):
        global bl_conf;
        lc_main = self.layout.column(align = False);
        lc_row = lc_main.row(align = True);
        lc_row.prop(scene(), 'm7a_morph_form_change', text="");
        lc_size = lc_row.row(align = True);
        lc_size.prop(scene(), 'm7a_morph_point_size_change', text="Size");
        lc_size.ui_units_x = 10;
        if (scene().m7a_morph_animate_by == "envl"):
            lc_main.prop(scene(), 'm7a_morph_envelope_change', text="Envelope Distance");
        lc_main.operator('3dmish.morph_apply_form', text='Apply');

class m7a_morph_start(operator):
    bl_idname      = '3dmish.morph_start'
    bl_label       = 'Start Morph'
    bl_description = 'Start Morphing Images'

    def execute(self, context):
        if (bpy.context.space_data.shading.type == 'SOLID'):
            bpy.context.space_data.shading.light = 'FLAT';
            bpy.context.space_data.shading.color_type = 'TEXTURE';

        global bl_info, morph_armature, morph_list_morphs;
        num = 1; x = 50; y = 50; xp = 0;
        scene_conf = scene();
        edit_collection = bpy.data.collections.new("M7A_Morph_Edit");
        bpy.context.scene.collection.children.link(edit_collection);
        
        bpy.context.scene.view_settings.view_transform = 'Standard';
        
        morph_main = bpy.data.objects.new("m7a_morph_data", None);
        lib_3dmish_link_obj_v1_0(morph_main, edit_collection);
        morph_main.location = (-10, 0, 0);
        morph_main["mish_main_morph"] = 1.0;
        
        morph_imgs = bpy.data.objects.new("m7a_morph_imgs", None);
        lib_3dmish_link_obj_v1_0(morph_imgs, edit_collection);
        morph_imgs.parent = morph_main;

        if bpy_u80:
            morph_main.empty_display_type = 'SPHERE';
            morph_main.empty_display_size = 0.5;
            #morph_main.hide_viewport = True;
            morph_imgs.hide_viewport = True;
        else:
            morph_main.empty_draw_type = 'SPHERE';
            morph_main.empty_draw_size = 0.5;
            #morph_main.hide = True;
            morph_imgs.hide = True;
        
        morph_main.hide_render = True;
        morph_imgs.hide_render = True;

        for img in scene_conf.m7a_morph_l.list:
            if (scene_conf.m7a_morph_ratio == True): x = scene_conf.m7a_morph_x; y = scene_conf.m7a_morph_y;
            else: x = 16; y = (img.file.size[1]/img.file.size[0])*16;
            
            number_img = str(num) if (len(str(num)) > 2) else "0" + str(num) if (len(str(num)) > 1) else "00" + str(num);
            morph_list_morphs[num] = m7a_morph_create_poly_plane("morph_image_" + number_img, x, y, edit_collection);
            morph_list_morphs[num].parent = morph_imgs;
            morph_list_morphs[num].location = (xp+10, 0, 0);

            if bpy_u80: morph_list_morphs[num].data.uv_layers.new();
            else:
                bpy.ops.object.select_all(action='DESELECT');
                lib_3dmish_obj_select_v1_0(morph_list_morphs[num]);
                bpy.ops.mesh.uv_texture_add();
                morph_list_morphs[num].show_transparent = True;

            material = m7a_morph_create_material(scene().render.engine, "m7a_morph_material_" + str(num), img);
            morph_list_morphs[num].data.materials.append(material);

            num += 1; xp += x + 2;
            ### END ###

        if bpy_d80: bpy.context.space_data.show_relationship_lines = False;
        else: bpy.context.space_data.overlay.show_relationship_lines = False;
        
        morph_forms = bpy.data.objects.new("m7a_morph_forms", None);
        lib_3dmish_link_obj_v1_0(morph_forms, edit_collection);
        morph_forms.parent = morph_main;
        
        create_form("m7a_morph_form_01", "dot",      morph_forms, edit_collection);
        create_form("m7a_morph_form_02", "box",      morph_forms, edit_collection);
        create_form("m7a_morph_form_03", "circle",   morph_forms, edit_collection);
        create_form("m7a_morph_form_04", "rhombus",  morph_forms, edit_collection);
        create_form("m7a_morph_form_05", "pointer",  morph_forms, edit_collection);
        create_form("m7a_morph_form_06", "triangle", morph_forms, edit_collection);
        create_form("m7a_morph_form_07", "star",     morph_forms, edit_collection);
        
        if bpy_u80: morph_forms.hide_viewport = True;
        else: morph_forms.hide = True;
        
        armdata = bpy.data.armatures.new('m7a_morph_armature_data');
        morph_armature = bpy.data.objects.new("m7a_morph_armature", armdata);
        lib_3dmish_link_obj_v1_0(morph_armature, edit_collection);
        morph_armature.parent = morph_main;
        morph_armature["mish_morph"] = 1.0;
        morph_armature["points"] = 0;
        
        bone_groups = morph_armature.pose.bone_groups;
        color_group = bone_groups.new(name="Color");
        color_group.color_set = 'CUSTOM';
        color_group.colors.normal = (0, 0, 0);
        color_group.colors.select = (0, 1, 0);
        color_group.colors.active = (1, 1, 1);

        selected_group = bone_groups.new(name="Selected");
        selected_group.color_set = 'CUSTOM';
        selected_group.colors.normal = (1, 0, 1);
        selected_group.colors.select = (1, 1, 0);
        selected_group.colors.active = (1, 1, 1);
        
        bpy.ops.object.select_all(action='DESELECT');
        lib_3dmish_obj_select_v1_0(morph_armature);
        bpy.context.view_layer.objects.active = morph_armature;
        bpy.ops.object.mode_set(mode='POSE', toggle=False);

        return {'FINISHED'};
      
def m7a_morph_point_form():
    return {
        "dot": {
            'vertex': [ (-0.4606965184211731, 0.016714558005332947, 0.19458986818790436),(-0.30550140142440796,0.016714543104171753,0.39579540491104126), 
                        (-0.06783051043748856,0.016714543104171753, 0.49543496966362),   ( 0.19458864629268646,0.016714543104171753,0.4606972634792328), 
                        ( 0.39579418301582336,0.01671457290649414,  0.30550214648246765),( 0.4954337477684021, 0.01671457290649414, 0.06783124804496765), 
                        ( 0.4606960415840149, 0.016714587807655334,-0.19458793103694916),( 0.30550092458724976,0.01671460270881653,-0.39579349756240845), 
                        ( 0.06783003360033035,0.01671460270881653, -0.4954330623149872), (-0.19458912312984467,0.01671460270881653,-0.4606953561306), 
                        (-0.39579465985298157,0.01671457290649414, -0.30550023913383484),(-0.4954342246055603, 0.01671457290649414,-0.06782931089401245), 
                        (-0.4606965184211731, 0.05014675855636597,  0.19458986818790436),(-0.30550140142440796,0.05014674365520477, 0.39579540491104126), 
                        (-0.06783051043748856,0.05014674365520477,  0.49543496966362),   ( 0.19458864629268646,0.05014674365520477, 0.4606972634792328), 
                        ( 0.39579418301582336,0.05014677345752716,  0.30550214648246765),( 0.4954337477684021, 0.05014677345752716, 0.06783124804496765), 
                        ( 0.4606960415840149, 0.050146788358688354,-0.19458793103694916),( 0.30550092458724976,0.05014680325984955,-0.39579349756240845), 
                        ( 0.06783003360033035,0.05014680325984955, -0.4954330623149872), (-0.19458912312984467,0.05014680325984955,-0.4606953561306), 
                        (-0.39579465985298157,0.05014677345752716, -0.30550023913383484),(-0.4954342246055603, 0.05014677345752716,-0.06782931089401245)], 
            'edges': [], 
            'faces': [ [0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1], [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], [4, 16, 15, 3], 
                       [7, 19, 18, 6], [21, 9, 10, 22], [11, 23, 22, 10], [1, 13, 12, 0], [8, 20, 19, 7],  [5, 17, 16, 4], 
                       [2, 14, 13, 1], [9, 21, 20, 8],  [6, 18, 17, 5],   [14, 2, 3, 15], [12, 23, 11, 0]]
        }, "box": {
            'vertex': [ (-0.9999999403953552, 0.0, -0.9999990463256836), (0.9999999403953552, 0.0, -0.9999990463256836), 
                        (-0.9999999403953552, 0.0,  1.0000009536743164), (0.9999999403953552, 0.0,  1.0000009536743164)], 
            'edges': [[2, 0], [0, 1], [1, 3], [3, 2]], 'faces': []
        }, "circle": { 'vertex': [(-0.9999999403953552, -9.5367431640625e-07, 9.5367431640625e-07), (-0.964267909526825, -9.5367431640625e-07, 0.2657851576805115), (-0.8634352087974548, -9.5367431640625e-07, 0.5046491622924805), (-0.7070469260215759, -1.0132789611816406e-06, 0.7070478200912476), (-0.5046482086181641, -1.0132789611816406e-06, 0.8634361028671265), (-0.26578420400619507, -1.0132789611816406e-06, 0.9642688035964966), (-2.842170943040401e-14, -9.5367431640625e-07, 1.0000009536743164), (0.2657841742038727, -1.0132789611816406e-06, 0.9642689228057861), (0.5046481490135193, -1.0132789611816406e-06, 0.863436222076416), (0.7070468068122864, -1.0132789611816406e-06, 0.7070479393005371), (0.8634350895881653, -9.5367431640625e-07, 0.5046492218971252), (0.9642677903175354, -9.5367431640625e-07, 0.26578518748283386), (0.9999998807907104, -9.5367431640625e-07, 9.5367431640625e-07), (0.964267909526825, -9.5367431640625e-07, -0.26578325033187866), (0.8634352087974548, -9.5367431640625e-07, -0.5046472549438477), (0.7070469260215759, -8.940696716308594e-07, -0.7070459127426147), (0.5046482086181641, -8.940696716308594e-07, -0.8634341955184937), (0.26578420400619507, -8.940696716308594e-07, -0.9642668962478638), (-2.842170943040401e-14, -8.940696716308594e-07, -0.9999990463256836), (-0.2657841742038727, -8.940696716308594e-07, -0.9642670154571533), (-0.5046481490135193, -8.940696716308594e-07, -0.8634343147277832), (-0.7070468068122864, -8.940696716308594e-07, -0.7070460319519043), (-0.8634350895881653, -9.5367431640625e-07, -0.5046473145484924), (-0.9642677903175354, -9.5367431640625e-07, -0.26578328013420105)], 'edges': [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17], [17, 18], [18, 19], [19, 20], [20, 21], [21, 22], [22, 23], [23, 0]], 'faces': []
        }, "pointer": {'vertex': [(0.0, 0.0, 0.2548255920410156), (-1.0, 0.0, 9.5367431640625e-07), (0.0, 0.0, 1.0000009536743164), (-0.4999999701976776, 0.0, -0.4999990463256836), (0.4999999701976776, 0.0, -0.4999990463256836), (-0.4999999701976776, 0.0, 0.5000009536743164), (0.4999999701976776, 0.0, 0.5000009536743164), (-0.2548246383666992, 0.0, 9.5367431640625e-07), (0.2548246383666992, 0.0, 9.5367431640625e-07), (1.0, 0.0, 9.5367431640625e-07), (0.0, 0.0, -0.2548236846923828), (0.0, 0.0, -0.9999990463256836), (0.0, 0.0, 0.03915254771709442), (-0.039151594042778015, 0.0, 9.5367431640625e-07), (0.039151594042778015, 0.0, 9.5367431640625e-07), (0.0, 0.0, -0.03915064036846161), (0.0, 0.012020706199109554, 0.03915254771709442), (-0.039151594042778015, 0.012020706199109554, 9.5367431640625e-07), (0.039151594042778015, 0.012020706199109554, 9.5367431640625e-07), (0.0, 0.012020706199109554, -0.03915064036846161)], 'edges': [[0, 2], [5, 3], [3, 4], [4, 6], [6, 5], [7, 1], [8, 9], [10, 11], [13, 12], [12, 14], [14, 15], [15, 13], [17, 16], [16, 18], [18, 19], [19, 17], [15, 19], [18, 14], [12, 16], [17, 13]], 'faces': []
        }, "rhombus": {
            'vertex': [(-0.9899494051933289, 0.0, 8.940696716308594e-07), (-4.17232506322307e-08, 0.0, -1.4142124652862549), 
                        (4.17232506322307e-08, 0.0, 1.4142143726348877), (0.9899494051933289, 0.0, 1.0132789611816406e-06)], 
            'edges': [[2, 0], [0, 1], [1, 3], [3, 2]], 'faces': []
        }, "triangle": {
            'vertex': [(-1.064989447593689, 0.0, -0.69916832447052), (1.064989447593689, 0.0, -0.69916832447052), 
                        (0.0, 0.0, 1.30083167552948)], 'edges': [[2, 0], [0, 1], [1, 2]], 'faces': []
        }, "star": {
            'vertex': [(-0.921392560005188, -9.834766387939453e-07, 0.3891787528991699), 
                        (-0.2258252203464508, -9.757040970725939e-07, 0.2925706207752228), 
                        (-0.1356605440378189, -1.0132789611816406e-06, 0.9908689856529236), 
                        (0.14383931457996368, -9.757040970725939e-07, 0.3405458331108093), 
                        (0.7915888428688049, -9.5367431640625e-07, 0.6110033392906189), 
                        (0.3662227988243103, -9.5367431640625e-07, 0.05014082044363022), 
                        (0.921392560005188, -9.238719940185547e-07, -0.3891768455505371), 
                        (0.2258252203464508, -9.316445357399061e-07, -0.29256871342658997), 
                        (0.1356605440378189, -8.940696716308594e-07, -0.9908670783042908), 
                        (-0.14383931457996368, -9.316445357399061e-07, -0.3405439257621765), 
                        (-0.7915888428688049, -9.5367431640625e-07, -0.6110014319419861), 
                        (-0.3662227988243103, -9.5367431640625e-07, -0.050138913094997406)], 
            'edges': [[11, 0], [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [10, 11]], 
            'faces': []
        }
    }

def create_form(name, code, parent, collection):
    data = m7a_morph_point_form()[code];
    obj = lib_3dmish_create_mesh_v1_0(name, name + "_mesh", data["vertex"], data["edges"], data["faces"], collection);
    obj.parent = parent;
    if bpy_u80: obj.hide_viewport = True;
    else: obj.hide = True;
    return obj;
    
def colored_points():
    pose = bpy.context.active_object.pose;
    bone_groups = pose.bone_groups;
    selected = bpy.context.selected_pose_bones;
    nmb_imgs = 0;
    
    for obj in m7a_morph_obj_get_children(bpy.context.active_object.parent):
        if (len(obj.name) >= 14):
            if (str(obj.name)[0:14] == "m7a_morph_imgs"):
                for img in m7a_morph_obj_get_children(obj):
                    nmb_imgs += 1;
    
    for bone in pose.bones:
        bone.bone_group = bone_groups.get("Color");
        
    for bone in selected:
        name = bone.name.split(".");
        for i in range(1, nmb_imgs+1):
            next_bone = pose.bones[name[0] + "." + name[1] + "." + str(i)];
            print(next_bone);
            next_bone.bone_group = bone_groups.get("Selected");
        bone.bone_group = bone_groups.get("Selected");
    
    pass

class m7a_morph_cancel(operator):
    bl_idname      = "3dmish.morph_cancel";
    bl_label       = "Cancel";
    bl_description = "Cancel Morph";

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
        a_obj = bpy.context.active_object;
        if (a_obj.get("mish_morph")) or (a_obj.get("mish_main_morph")):
            collection = bpy.context.active_object.users_collection[0]
            for obj in collection.objects:
                if (obj.users == 1):
                    bpy.data.objects.remove(obj);
            bpy.data.collections.remove(collection);
        bpy.ops.object.select_all(action='DESELECT');
        return {'FINISHED'};

class m7a_morph_edit(operator):
    bl_idname      = "3dmish.morph_edit";
    bl_label       = "Edit Morph";
    bl_description = "Edit Morphing";

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
        a_obj = bpy.context.active_object;
        if (a_obj.get("mish_morph")):
            m7a_morph_edit_func(a_obj);
        elif (a_obj.get("mish_main_morph")):
            for obj in m7a_morph_obj_get_children(a_obj):
                if (obj.get("mish_morph")):
                    m7a_morph_edit_func(obj);
                    break;
        return {'FINISHED'};

def lib_3dmish_create_mesh_from_points_v1_0(name, namemesh, vertices, img, collection = None, img_points = True):

    if (img_points == True):
        for img_ver in img.data.vertices:
            vertices.append(img_ver.co);
    verts, edges, faces, overts, oedges, ofaces = delaunay_2d_cdt([v.to_2d() for v in vertices], [], [], 0, 0.1);
    verts = [(v.x, v.y, 0) for i, v in enumerate(verts)];

    new_mesh = bpy.data.meshes.new(namemesh);
    new_mesh.from_pydata(verts, edges, faces);
    new_mesh.update();

    obj = bpy.data.objects.new(name, new_mesh);
    obj.parent = img.parent.parent;
    obj.location = img.location;
    obj.scale = (1, 1, 1);

    lib_3dmish_link_obj_v1_0(obj, collection);
    
    return obj
    
def lib_3dmish_link_obj_v1_0(obj, collection = None):
    if bpy_u80:
        if (collection != None):
            collection.objects.link(obj);
        else:
            scene().collection.objects.link(obj);
    else: scene().objects.link(obj);
    bpy.context.view_layer.update() if bpy_u80 else scene().update();

def lib_3dmish_create_mesh_v1_0(name, namemesh, vertex, edges, faces, collection = None):
    mesh = bpy.data.meshes.new(namemesh); obj = bpy.data.objects.new(name, mesh); lib_3dmish_link_obj_v1_0(obj, collection);
    mesh.from_pydata(vertex, edges, faces); mesh.update(calc_edges=True);
    return obj
    
def lib_3dmish_obj_select_v1_0(obj):
    if bpy_d80: obj.select = True;
    else: obj.select_set(state = True);
    
def m7a_morph_edit_func(obj):
    bpy.ops.object.select_all(action='DESELECT');
    lib_3dmish_obj_select_v1_0(obj);
    bpy.context.view_layer.objects.active = obj;
    bpy.ops.object.mode_set(mode='POSE', toggle=False);

class m7a_morph_back(operator):
    bl_idname      = "3dmish.morph_back_to_main";
    bl_label       = "Back To Main";
    bl_description = "Back To Main";

    def execute(self, context):
        global bl_info; bl_conf["panel"] = "main";
        return {'FINISHED'};
        
class mish_moprh_aspect_ratio(operator):
    bl_idname = "3dmish.moprh_aspect_ratio"; bl_label = "";
    bl_description = "Calculate aspect ratio";

    def execute(self, context):
        morph_l = scene().m7a_morph_l;
        img = morph_l.list[0];
        scene().m7a_morph_y = (img.file.size[1]/img.file.size[0])*scene().m7a_morph_x;
        return {"FINISHED"};

class m7a_morph_add_img_file(operator):
    bl_idname      = '3dmish.moprh_add_image';
    bl_label       = 'Add Image';
    bl_description = 'Add image for morph';

    def execute(self, context):
        morph_l = scene().m7a_morph_l;
        item = morph_l.list.add(); item.name = "None"; item.id = len(morph_l.list)-1;
        scene().m7a_morph_index = len(morph_l.list) - 1;
        return {'FINISHED'};

class lc_btn:
    icon = "NONE"; icon_value = 0;
    prew = bpy.utils.previews.new();
    enabled = True; lc_main = None;
    
    def __init__(self, lc): self.lc_main = lc;
    def icon_sys(self, ic_code): self.icon = ic_code;
    
    def icon_file(self, ic_file):
        try: self.prew.load(ic_file, ic_file, 'IMAGE');
        except: pass
        try: self.icon_value = icons_dict[ic_file].icon_id;
        except: pass
    
    def create(self, path, label, icon_value, icon, description):
        self.btn = self.lc_main.operator(path, text=label, icon_value=icon_value, icon=icon);
        if (description != ""): self.btn = description;
        
    def disable(self): self.lc_main.enabled = False; self.enabled = False;
    def enable(self):  self.lc_main.enabled = True;  self.enabled = True;

def lc_button(lc_main, path, label, icon, description = ""):
    button = lc_btn(lc_main);
    
    if (os.path.exists(icon)): button.icon_file(icon);
    else: button.icon_sys(icon);

    button.create(path, label, button.icon_value, button.icon, description);
    return button;
    
class m7a_morph_remove_img_file(operator):
    bl_idname      = '3dmish.moprh_remove_image';
    bl_label       = 'Remove Image';
    bl_description = 'Remove image from morph';

    def execute(self, context):
        scene().m7a_morph_index -= 1;
        morph_l = scene().m7a_morph_l;
        morph_l.list.remove(morph_l.active);
        return {'FINISHED'};

class m7a_morph_move_up_image(operator):
    bl_idname      = '3dmish.morph_move_up_image';
    bl_label       = 'Move Up Image';
    bl_description = 'Move up selected image';

    def execute(self, context):
        morph_l = scene().m7a_morph_l;
        morph_l.list.move(morph_l.active, morph_l.active-1);
        morph_l.active -= 1;
        return {'FINISHED'};

class m7a_morph_move_down_image(operator):
    bl_idname      = '3dmish.morph_move_down_image';
    bl_label       = 'Move Down Image';
    bl_description = 'Move down selected image';

    def execute(self, context):
        morph_l = scene().m7a_morph_l;
        morph_l.list.move(morph_l.active, morph_l.active+1);
        morph_l.active += 1;
        return {'FINISHED'};
        
class m7a_morph_apply_form(operator):
    bl_idname      = '3dmish.morph_apply_form';
    bl_label       = 'Apply';
    bl_description = 'Apply form to selected point(s)';

    def execute(self, context):
        morph_armature = bpy.context.active_object;
        selected = bpy.context.selected_pose_bones;
        nmb_imgs = 0; pose = morph_armature.pose;
        morph_list_forms_obj = [];
        
        for obj in m7a_morph_obj_get_children(morph_armature.parent):
            if (len(obj.name) >= 14):
                if (str(obj.name)[0:14] == "m7a_morph_imgs"):
                    for img in m7a_morph_obj_get_children(obj):
                        nmb_imgs += 1;
            try:
                if (obj.name[0:15] == "m7a_morph_forms"):
                    for form in m7a_morph_obj_get_children(obj):
                        morph_list_forms_obj.append(form);
            except: pass
                    
        for bone in selected:
            name = bone.name.split(".");
            for i in range(1, nmb_imgs+1):
                ic = 0;
                for form in morph_list_form:
                    if scene().m7a_morph_form_change == form[0]:
                        point = pose.bones[name[0] + "." + name[1] + "." + str(i)];
                        point.custom_shape = morph_list_forms_obj[ic];
                        if (bpy_u3):
                            point.custom_shape_scale_xyz = (
                                scene().m7a_morph_point_size_change/10,
                                scene().m7a_morph_point_size_change/10,
                                scene().m7a_morph_point_size_change/10
                            );
                        else:
                            point.custom_shape_scale = scene().m7a_morph_point_size_change/10;
                        
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False);
                        
                        point = morph_armature.data.edit_bones[name[0] + "." + name[1] + "." + str(i)];
                        point.envelope_distance = scene().m7a_morph_envelope_change;
                        
                        bpy.ops.object.mode_set(mode='POSE', toggle=False);
                    ic += 1;
                    
        return {'FINISHED'};

class m7a_morph_add_point(operator):
    bl_idname      = '3dmish.morph_add_point'
    bl_label       = 'Add Point'
    bl_description = 'Add point for morph'

    def execute(self, context):
        obj = bpy.data.objects; morph_list_forms_obj = []; main_point = None;
        #try:
        if (1 == 1):
            if (bpy.context.active_object["mish_morph"]):
                morph_armature = bpy.context.active_object;
                    
                for forms in m7a_morph_obj_get_children(morph_armature.parent):
                    try:
                        if (forms.name[0:15] == "m7a_morph_forms"):
                            for form in m7a_morph_obj_get_children(forms):
                                morph_list_forms_obj.append(form);
                    except: pass
                    
                nmb = str(morph_armature["points"]+1); im = 1;
                                                                    
                if (obj.get("m7a_morph_imgs") != None):
                    moving = mathutils.Vector((0, 0, 0)); tmp_morph = None;
                    if (scene().m7a_morph_opts == "3d_cursor"):
                        for morph in m7a_morph_obj_get_children(obj['m7a_morph_imgs']):
                            x = scene().m7a_morph_x/2;
                            y = scene().m7a_morph_y/2;
                            loc_min = morph.matrix_world.translation - mathutils.Vector((x, y, 0));
                            loc_max = morph.matrix_world.translation + mathutils.Vector((x, y, 0));
                            cursor = bpy.context.scene.cursor.location;
                            if (loc_min.x <= cursor.x) and (loc_max.x >= cursor.x):
                                moving = cursor - morph.matrix_world.translation;
                                tmp_morph = morph;
                            
                    for morph in m7a_morph_obj_get_children(obj['m7a_morph_imgs']):
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False);
                        point = morph_armature.data.edit_bones.new('point.'+ nmb + "." + str(im));
                        point.head = morph.location;
                        point.tail = morph.location + mathutils.Vector((0.0, 0.0, 1.0));
                        point.envelope_distance = scene().m7a_morph_envelope;
                        point_name = point.name;
                        
                        bpy.ops.object.mode_set(mode='POSE', toggle=False); ic = 0;
                        if (tmp_morph == morph) or (tmp_morph == None):
                            if (main_point == None):
                                main_point = bpy.context.object.pose.bones[point_name];
                        
                        if (scene().m7a_morph_opts == "3d_cursor"):
                            point = bpy.context.object.pose.bones[point_name];
                            point.location = mathutils.Vector((moving.x, 0, -moving.y));
                        else: pass
                        
                        if (morph_list_forms_obj != []):
                            for form in morph_list_form:
                                if scene().m7a_morph_form == form[0]:
                                    point = bpy.context.object.pose.bones[point_name];
                                    point.custom_shape = morph_list_forms_obj[ic];
                                    if (bpy_u3):
                                        point.custom_shape_scale_xyz = (scene().m7a_morph_point_size/10, 
                                        scene().m7a_morph_point_size/10, scene().m7a_morph_point_size/10);
                                    else:
                                        point.custom_shape_scale = scene().m7a_morph_point_size/10;
                                    const = point.constraints.new(type='LIMIT_LOCATION');
                                    const.use_min_x = True; const.min_x = -(morph.dimensions.x/2);
                                    const.use_max_x = True; const.max_x = morph.dimensions.x/2;
                                    const.use_min_y = True;
                                    const.use_max_y = True;
                                    const.use_min_z = True; const.min_z = -(morph.dimensions.y/2);
                                    const.use_max_z = True; const.max_z = morph.dimensions.y/2;
                                    const.use_transform_limit = True;
                                    const.owner_space = 'LOCAL';
                                ic += 1;
                        im += 1;

                    bpy.ops.object.mode_set(mode='POSE', toggle=False);
                    morph_armature["points"] = morph_armature["points"]+1;
                    if (main_point != None):
                        bpy.ops.pose.select_all(action='DESELECT');
                        main_point.bone.select = True;
                        colored_points();
        #except: pass
        return {'FINISHED'};

class m7a_morph_remove_point(operator):
    bl_idname      = '3dmish.morph_remove_point'
    bl_label       = 'Remove Point'
    bl_description = 'Remove selected point from morph'

    def execute(self, context):
        morph_armature = bpy.context.active_object;
        selected = bpy.context.selected_pose_bones;
        nmb_imgs = 0; pose = morph_armature.pose;
        
        for obj in m7a_morph_obj_get_children(morph_armature.parent):
            if (len(obj.name) >= 14):
                if (str(obj.name)[0:14] == "m7a_morph_imgs"):
                    for img in m7a_morph_obj_get_children(obj):
                        nmb_imgs += 1;
                        
        for bone in selected:
            name = bone.name.split(".");
            for i in range(1, nmb_imgs+1):
                next_bone = pose.bones[name[0] + "." + name[1] + "." + str(i)];
                bpy.ops.object.mode_set(mode='EDIT', toggle=False);
                morph_armature.data.edit_bones.remove(morph_armature.data.edit_bones[next_bone.name]);
                bpy.ops.object.mode_set(mode='POSE', toggle=False);
        
        return {'FINISHED'};

class m7a_morph_create_line(operator):
    bl_idname      = '3dmish.morph_create_line'
    bl_label       = 'Create line between two points'
    bl_description = 'Create line between two selected points'

    def execute(self, context):
        return {'FINISHED'};

class m7a_morph_remove_line(operator):
    bl_idname      = '3dmish.morph_remove_line'
    bl_label       = 'Remove line between two points'
    bl_description = 'Remove line between two selected points'

    def execute(self, context):
        return {'FINISHED'};

class m7a_morph_show_selected(operator):
    bl_idname       = '3dmish.morph_show_selected'
    bl_label        = 'Activate Point'
    bl_description  = 'Activate Selected Point'

    def execute(self, context):
        colored_points();
        return {'FINISHED'};
        
class m7a_morph_preview(operator):
    bl_idname       = '3dmish.morph_preview'
    bl_label        = 'Preview Morphing'
    bl_description  = 'Create preview morphing'

    def execute(self, context):
        list_imgs, new_imgs = create_morph(self);
        for i in range(0, len(new_imgs)):
            new_imgs[i].location = (list_imgs[i].location.x-10, list_imgs[i].dimensions.y+2, 0);
        self.report({'INFO'}, "Preview is Created!");
        return {'FINISHED'};

class m7a_morph_create(operator):
    bl_idname       = '3dmish.morph_create'
    bl_label        = 'Create Morphing'
    bl_description  = 'Create morphing images'

    def execute(self, context):
        try: bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
        except: pass
        
        bpy.ops.object.select_all(action='DESELECT');
        list_imgs, new_imgs = create_morph(self);
        z = 0.0; zp = 0.01;
        for i in range(0, len(new_imgs)):
            new_imgs[i].location = new_imgs[i].location + mathutils.Vector((0, 0, -z));
            z += zp;
            lib_3dmish_obj_select_v1_0(new_imgs[i]);
            if (i == 0): bpy.context.view_layer.objects.active = new_imgs[i];
            
        bpy.ops.object.join(); obj = bpy.context.active_object;
        max_len = float(len(new_imgs)) if (scene().m7a_morph_loop == True) else float(len(new_imgs)-1);
        if (bpy_u3):
            new_imgs[0]['Animation'] = 0.0;
            new_imgs[0].id_properties_ensure();
            pm = new_imgs[0].id_properties_ui("Animation");
            pm.update(min=0, max=max_len, soft_min=0, soft_max=max_len);
        else:
            obj["_RNA_UI"] = {};
            new_imgs[0]['Animation'] = 0.0;
            obj["_RNA_UI"]['Animation'] = {
                "min":0.0, "max":max_len, 
                "soft_min":0.0, "soft_max":max_len, 
                "description":"Grag to Animate Morphing!"
            };
        
        for i in range(0, len(list_imgs)):
            mix = new_imgs[0].data.materials[i].node_tree.nodes.get("Mix");
            if (i == 0):
                add_driver(mix.inputs[0], "default_value", [
                    ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                        [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)],
                        [(1.0, 1.0), (1.0, 1.0), (1.0, 1.0)],
                        [(len(list_imgs)-1, 1.0), (len(list_imgs)-1, 1.0), (len(list_imgs)-1, 1.0)],
                        [(len(list_imgs), 0.0), (len(list_imgs), 0.0), (len(list_imgs), 0.0)],
                    ]]
                ]);
            else:
                if (scene().m7a_morph_transparent == True):
                    add_driver(mix.inputs[0], "default_value", [
                        ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                            [(i-1.0, 1.0), (i-1.0, 1.0), (i-1.0, 1.0)],
                            [(i+0.0, 0.0), (i-0.0, 0.0), (i+0.0, 0.0)],
                            [(i+1.0, 1.0), (i+1.0, 1.0), (i+1.0, 1.0)],
                        ]]
                    ]);
                else:
                    if (i < (len(list_imgs)-1)):
                        add_driver(mix.inputs[0], "default_value", [
                            ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                                [(i+0.0, 0.0), (i-0.0, 0.0), (i+0.0, 0.0)],
                                [(i+1.0, 1.0), (i+1.0, 1.0), (i+1.0, 1.0)],
                            ]]
                        ]);
        
        xm = 2; ym = 1;
        
        for i in range(1, len(new_imgs[0].data.shape_keys.key_blocks)):
            if (i == 1):
                add_driver(new_imgs[0].data.shape_keys.key_blocks[i], "value", [
                    ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                        [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)],
                        [(1.0, 1.0), (1.0, 1.0), (1.0, 1.0)],
                        [(len(list_imgs)-1, 0.0), (len(list_imgs)-1, 0.0), (len(list_imgs)-1, 0.0)],
                    ]]
                ]);
            elif (i == 2):
                add_driver(new_imgs[0].data.shape_keys.key_blocks[i], "value", [
                    ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                        [(len(list_imgs)-0.999, 0.0), (len(list_imgs)-0.999, 0.0), (len(list_imgs)-0.999, 0.0)],
                        [(len(list_imgs)-1, 1.0), (len(list_imgs)-1, 1.0), (len(list_imgs)-1, 1.0)],
                        [(len(list_imgs), 0.0), (len(list_imgs), 0.0), (len(list_imgs), 0.0)],
                    ]]
                ]);
            else:
                if (i % 2) == 0:
                    add_driver(new_imgs[0].data.shape_keys.key_blocks[i], "value", [
                        ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                            [((i-ym-1)-1.0, 0.0), ((i-ym-1)-1.0, 0.0), ((i-ym-1)-1.0, 0.0)],
                            [((i-ym-1)+0.0, 1.0), ((i-ym-1)+0.0, 1.0), ((i-ym-1)+0.0, 1.0)],
                        ]]
                    ]);
                    ym += 1;
                else:
                    add_driver(new_imgs[0].data.shape_keys.key_blocks[i], "value", [
                        ["Variable", "SINGLE_PROP", a_obj(), '["Animation"]', [
                            [((i-xm-1), 1.0), ((i-xm-1), 1.0), ((i-xm-1), 1.0)],
                            [((i-xm-1)+1.0, 0.0), ((i-xm-1)+1.0, 0.0), ((i-xm-1)+1.0, 0.0)],
                        ]]
                    ]);
                    xm += 1;
                    
        collection = None;
        try:
            collection = bpy.data.collections["M7A_Morph_Final"];
        except:
            collection = bpy.data.collections.new("M7A_Morph_Final");
            bpy.context.scene.collection.children.link(collection);
        
        old_col = new_imgs[0].users_collection[0];
        old_col.objects.unlink(new_imgs[0]);
        lib_3dmish_link_obj_v1_0(new_imgs[0], collection);
        old_col.hide_viewport = True;
        old_col.hide_render = True;
        
        new_imgs[0].select_set(True);
        bpy.context.view_layer.objects.active = new_imgs[0];
        
        len_slots = len(new_imgs[0].material_slots);
        ig = len_slots-1;
        for i in range(0, len_slots-1):
            new_imgs[0].active_material_index = 0;
            for p in range(0, ig):
                bpy.ops.object.material_slot_move(direction='DOWN');
            if (ig > 0): ig -= 1;
        
        self.report({'INFO'}, "Morphing is Created!");
        return {'FINISHED'};

def add_driver(obj, path, variables):
    obj.driver_remove(path);
    driver = obj.driver_add(path);
    driver.driver.type="AVERAGE";
    driver.modifiers.remove(driver.modifiers[0]);
    
    if (variables != []):
        for var in variables:
            variable = driver.driver.variables.new();
            variable.name=var[0];
            variable.type=var[1];
            
            if (var[1] == "SINGLE_PROP"):
                target = variable.targets[0];
                target.id = var[2];
                target.data_path = var[3];
            elif (var[1] == "LOC_DIFF"):
                target = variable.targets[0];
                target.id = var[2];
                target.bone_target = var[3];
                target = variable.targets[1];
                target.id = var[5];
                target.bone_target = var[6];
            
            if (var[4] != []):
                i = 1;
                for co in var[4]:
                    driver.keyframe_points.add(1);
                    point = driver.keyframe_points[i-1];
                    point.co = co[0];
                    try:
                        point.handle_left_type = 'FREE';
                        point.handle_left = co[1];
                        point.handle_right_type = 'FREE';
                        point.handle_right = co[2];
                    except:
                        point.interpolation = 'LINEAR';
                        point.co = co[0];
                    i += 1;


class m7a_morph_btn(operator):
    bl_idname = "mish_morph.btn"; bl_label  = "";
    bl_btn: str_prop(); bl_opt: str_prop(); bl_desc: str_prop();
    
    @classmethod
    def description(cls, context, properties): return properties.bl_desc;

    def execute(self, context):
        if (self.bl_btn == "jump_to_point"):
            morph_armature = bpy.context.active_object;
            selected = bpy.context.selected_pose_bones[0];
            nmb_imgs = 0; pose = morph_armature.pose;
            
            for obj in m7a_morph_obj_get_children(morph_armature.parent):
                if (len(obj.name) >= 14):
                    if (str(obj.name)[0:14] == "m7a_morph_imgs"):
                        for img in m7a_morph_obj_get_children(obj):
                            nmb_imgs += 1;
            
            name = selected.name.split(".");
            num = int(name[2]) + int(self.bl_opt);
            bone_name = name[0] + "." + name[1] + "." + str(num);
            if (bone_name in morph_armature.pose.bones):
                self.report({'INFO'}, "Select next point: " + str(bone_name));
                bpy.ops.pose.select_all(action='DESELECT');
                #morph_armature.pose.bones.active = morph_armature.bones[bone_name].bone;
                morph_armature.pose.bones[bone_name].bone.select = True;
                bpy.ops.view3d.view_selected(use_all_regions=False);
            
                for i in range(0, 23): bpy.ops.view3d.zoom(delta=-1);
            
        elif (self.bl_btn == "jump_to_back"):
            pass

        return {'FINISHED'};

def create_morph(self):
    morph_armature = bpy.context.active_object;
    if (morph_armature):
        obj = bpy.data.objects;
        list_morphs = [morph for morph in m7a_morph_obj_get_children(obj['m7a_morph_imgs'])];
        list_obj_morph = []; list_rig = get_pic_rig(list_morphs);
        #print(list_morphs);
        
        if (scene().m7a_morph_method == "sub"):
            for i in range(0, len(list_morphs)):
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
                bpy.ops.object.select_all(action='DESELECT');
                lib_3dmish_obj_select_v1_0(list_morphs[i]);
                bpy.ops.object.duplicate();
                
                obj_m = bpy.context.selected_objects[0];
                obj_m.parent = obj_m.parent.parent;
                
                modifier = obj_m.modifiers.new(name="M7A Subs", type='SUBSURF');
                modifier.subdivision_type = 'SIMPLE';
                modifier.levels = scene().m7a_morph_subdevision;
                
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
                bpy.ops.object.select_all(action='DESELECT');
                lib_3dmish_obj_select_v1_0(obj_m);
                if (bpy_u3): bpy.context.view_layer.objects.active = obj_m;
                bpy.ops.object.modifier_apply(modifier=obj_m.modifiers[0].name);
                
                old_material = list_morphs[i].data.materials[0];
                material = m7a_morph_create_material(
                    scene().render.engine, 
                    "m7a_morph_material_" + str(i),
                    old_material.node_tree.nodes.get("Image Texture").image,
                    "Morph"
                );
                obj_m.data.materials.clear();
                obj_m.data.materials.append(material);
                
                list_obj_morph.append(obj_m);
            
        elif (scene().m7a_morph_method == "del"):
            for i in range(0, len(list_morphs)):
                list_points_img = [];
                for b in list_rig[i]:
                    bone_s = bpy.context.object.pose.bones[b.name].location;
                    list_points_img.append(mathutils.Vector((bone_s.x, -bone_s.z, bone_s.y)));
                
                obj_m = lib_3dmish_create_mesh_from_points_v1_0(
                    "morph_img_mod_"+str(i),
                    "morph_img_mesh_"+str(i),
                    list_points_img,
                    list_morphs[i],
                    list_morphs[i].users_collection[0],
                    scene().m7a_morph_use_vrtx
                );
                
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
                bpy.ops.object.select_all(action='DESELECT');
                lib_3dmish_obj_select_v1_0(obj_m);
                bpy.context.view_layer.objects.active = obj_m;
                bpy.ops.object.mode_set(mode='EDIT', toggle=False);
                bm = bmesh.from_edit_mesh(obj_m.data);
                uv_layer = bm.loops.layers.uv.verify();
                vrx = list_morphs[i].data.vertices[3].co;
                for face in bm.faces:
                    for loop in face.loops:
                        loop_uv = loop[uv_layer];
                        loop_uv.uv = (((loop.vert.co.x-vrx.x)/(vrx.x*2))+1, (loop.vert.co.y+vrx.y)/(vrx.y*2));
                bmesh.update_edit_mesh(obj_m.data);
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
                bpy.ops.object.select_all(action='DESELECT');
                lib_3dmish_obj_select_v1_0(morph_armature);
                bpy.context.view_layer.objects.active = morph_armature;
                bpy.ops.object.mode_set(mode='POSE', toggle=False);
                
                old_material = list_morphs[i].data.materials[0];
                material = m7a_morph_create_material(
                    scene().render.engine, 
                    "m7a_morph_material_" + str(i),
                    old_material.node_tree.nodes.get("Image Texture").image,
                    "Morph"
                );
                obj_m.data.materials.append(material);
                
                list_points_img = [];
                list_obj_morph.append(obj_m);
        
        
        lib_3dmish_obj_select_v1_0(morph_armature);
        if (bpy_u3): bpy.context.view_layer.objects.active = morph_armature;
        bpy.ops.object.mode_set(mode='POSE', toggle=False);
                
        list_loc = {};
        for i_ln in list_rig:
            for bone in i_ln:
                list_loc[bone.name] = bpy.context.object.pose.bones[bone.name].location;
            
        for i in range(0, len(list_obj_morph)):
            if (i > 0) and (i < len(list_obj_morph)-1):
                lib_3dmish_create_image_rig(self, list_obj_morph, [i, i-1, i+1], list_rig, list_loc, list_morphs);
            elif (i >= len(list_obj_morph)-1):
                lib_3dmish_create_image_rig(self, list_obj_morph, [i, i-1, 0], list_rig, list_loc, list_morphs, True);
            else:
                lib_3dmish_create_image_rig(self, list_obj_morph, [i, i+1, len(list_obj_morph)-1], list_rig, list_loc, list_morphs);
                        
        return (list_morphs, list_obj_morph);
    else: return (None, None);
    
def lib_3dmish_create_image_rig(self, img, ln, pos, list_loc, old_img, if_n = False):
    i = ln[0]; img_loc_tmp = img[i].location;
    
    #self.report({'INFO'}, str(ln))
    
    sec = (1,);
    try:
        if (ln[2]): sec = (1, 2);
    except: pass
    
    if (if_n): sec = (1, 2);
    
    for s in sec:
        try: bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
        except: pass
        
        armdata = bpy.data.armatures.new('m7a_morph_data_'+img[i].name+"_"+str(i));
        morph_armature = bpy.data.objects.new("m7a_morph_armature_"+img[i].name+"_"+str(i), armdata);
        lib_3dmish_link_obj_v1_0(morph_armature, img[i].users_collection[0]);
        morph_armature.parent = img[i].parent;
        morph_armature.location = img[i].location;
        
        bpy.ops.object.select_all(action='DESELECT');
        lib_3dmish_obj_select_v1_0(morph_armature);
        bpy.context.view_layer.objects.active = morph_armature;
        
        for p in range(len(pos[i])):
            bpy.ops.object.mode_set(mode='EDIT', toggle=False);
            bone_s = list_loc[pos[i][p].name];
            point = morph_armature.data.edit_bones.new("pn." + str(pos[i][p].name));
            point.head = mathutils.Vector((bone_s.x, -bone_s.z, bone_s.y));
            point.tail = mathutils.Vector((bone_s.x, -bone_s.z, bone_s.y)) + mathutils.Vector((0.0, 0.0, 1.0));
            point.envelope_distance = pos[i][p].envelope_distance;
            point_name = point.name;
            
            bpy.ops.object.mode_set(mode='POSE', toggle=False);
            point = bpy.context.object.pose.bones[point_name];
            point.location = list_loc[pos[ln[s]][p].name] - list_loc[pos[ln[0]][p].name];
            
        if (scene().m7a_morph_borders == True):
            vrx = old_img[i].data.vertices[0].co;
            Xre = (-vrx.x*2)/20; Yre = (-vrx.y*2)/20;
            Xor = vrx.x; Yor = vrx.y;
            for n in range(20):
                bpy.ops.object.mode_set(mode='EDIT', toggle=False);
                
                point = morph_armature.data.edit_bones.new("pn." + str(pos[i][p].name));
                pos_point = mathutils.Vector((vrx.x, Yor, vrx.z));
                point.head = pos_point; point.tail = pos_point + mathutils.Vector((0.0, 0.0, 1.0));
                
                point = morph_armature.data.edit_bones.new("pn." + str(pos[i][p].name));
                pos_point = mathutils.Vector((Xor, vrx.y, vrx.z));
                point.head = pos_point; point.tail = pos_point + mathutils.Vector((0.0, 0.0, 1.0));
                
                point = morph_armature.data.edit_bones.new("pn." + str(pos[i][p].name));
                pos_point = mathutils.Vector((-vrx.x, Yor, vrx.z));
                point.head = pos_point; point.tail = pos_point + mathutils.Vector((0.0, 0.0, 1.0));
                
                point = morph_armature.data.edit_bones.new("pn." + str(pos[i][p].name));
                pos_point = mathutils.Vector((Xor, -vrx.y, vrx.z));
                point.head = pos_point; point.tail = pos_point + mathutils.Vector((0.0, 0.0, 1.0));
                
                Yor += Yre; Xor += Xre;
            
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False);
        
        bpy.ops.object.select_all(action='DESELECT');
        lib_3dmish_obj_select_v1_0(img[i]);
        lib_3dmish_obj_select_v1_0(morph_armature);
        bpy.context.view_layer.objects.active = morph_armature;
        
        img[i].location = img_loc_tmp;
        if (scene().m7a_morph_animate_by == "auto"):
            bpy.ops.object.parent_set(type='ARMATURE_AUTO');
        else:
            bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE');
        bpy.context.view_layer.objects.active = img[i];
        img[i].location = (0, 0, 0);
        name_modifier = img[i].name + "_sk_"+str(s);
        bpy.context.object.modifiers[len(img[i].modifiers)-1].name = name_modifier;
        bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=False, modifier=name_modifier);
        
        bpy.ops.object.select_all(action='DESELECT');
        
        lib_3dmish_obj_select_v1_0(morph_armature);
        bpy.context.view_layer.objects.active = morph_armature;
        bpy.ops.object.delete();
        
    return img;
  
def get_pic_rig(morphs):
    global morph_list_morphs;
    result = []; obj = bpy.data.objects;
    morph_armature = bpy.context.active_object;
    
    for morph in morphs: result.append([]);
    
    if (morph_armature["mish_morph"]):
        for bone in morph_armature.data.bones:
            result[int(bone.name.split(".")[2])-1].append(bone);
    
    return result;

class m7a_morph_list_file(prop_group):
    file: point_prop(name = "Image", type = bpy.types.Image);
    id: int_prop();

class m7a_morph_list(prop_group):
    active: int_prop();
    list:collect_prop(type = m7a_morph_list_file, name = "Images");

class m7a_morph_items(ui_list):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        lc_main = layout;
        lc_main.label(text="", icon="FORWARD", text_ctxt="");
        lc_main.template_ID(item, "file", open="image.open");
    
def m7a_morph_obj_get_children(sel_object): 
    result = [];
    for obj in bpy.data.objects: 
        if obj.parent == sel_object: 
            result.append(obj);
    return result 
    
def m7a_morph_create_poly_plane(name, x, y, collection = None):
    mesh = bpy.data.meshes.new(name+"_mesh"); obj = bpy.data.objects.new(name, mesh); scn = bpy.context.scene;
    lib_3dmish_link_obj_v1_0(obj, collection);
    lib_3dmish_obj_select_v1_0(obj); gV = [(-(x/2), -(y/2), 0.0),(x/2, -(y/2), 0.0),(-(x/2), y/2, 0.0),(x/2, y/2, 0.0)];
    gF = [(0, 1, 3, 2)]; mesh.from_pydata(gV, [], gF); mesh.update();
    return obj;

def m7a_morph_create_material(type, name, img, morph_type = "None", diffuse = (1, 1, 1), specular = (1, 1, 1), alpha = 1):
    material = bpy.data.materials.new(name);

    if (type == "BLENDER_RENDER"):
        material.diffuse_color     = diffuse;     material.diffuse_shader     = 'LAMBERT';
        material.diffuse_intensity = 1.0;         material.specular_color     = specular;
        material.specular_shader   = 'COOKTORR';  material.specular_intensity = 0;
        material.alpha             = alpha;       material.use_shadeless      = 1;
        material.ambient           = 1;
        texture = bpy.data.textures.new('m7a_morph_texture', type = 'IMAGE');
        texture.image = img.file; material.texture_slots.add().texture = texture;
        
    elif (type == "BLENDER_EEVEE") or (type == "CYCLES"):
        material.use_nodes = True;
        material.blend_method = 'BLEND';
        material.shadow_method = 'NONE';
        #material.show_transparent_back = False;

        nodes = material.node_tree.nodes;
        links = material.node_tree.links;

        while(nodes): nodes.remove(nodes[0]);

        mat_output = nodes.new("ShaderNodeOutputMaterial"); mat_output.location = 500, 100;
        
        tex_image = nodes.new("ShaderNodeTexImage");
        tex_image.location  = -500, 100;
        tex_image.extension = 'CLIP';
        
        if (morph_type == "None"):
            tex_image.image = img.file;
            
            principled = nodes.new("ShaderNodeBsdfPrincipled");
            principled.location = 0, 100;
            principled.inputs[5].default_value = 0;
            principled.inputs[18].default_value = 0;
            #principled.inputs[18].default_value = 0;
            
            links.new(mat_output.inputs['Surface'], principled.outputs['BSDF']);
            links.new(principled.inputs[0], tex_image.outputs['Color']);
            links.new(principled.inputs[17], tex_image.outputs['Color']);
            links.new(principled.inputs[19], tex_image.outputs['Alpha']);
            
        elif (morph_type == "Morph"):
            tex_image.image = img;
            
            emission = nodes.new("ShaderNodeEmission");
            emission.location = 0, 100;
            mix = nodes.new("ShaderNodeMixRGB");
            mix.location = -200, -320;
            mix.name = "Mix";
            mix.inputs[0].default_value = 0;
            mix.inputs[2].default_value = (0, 0, 0, 1);
            
            transparent = nodes.new("ShaderNodeBsdfTransparent");
            transparent.location = 200, 100;
            
            mixshader = nodes.new("ShaderNodeMixShader");
            mixshader.location = 150, 0;

            links.new(mixshader.inputs[0], mix.outputs['Color']);
            links.new(mixshader.inputs[1], transparent.outputs['BSDF']);
            links.new(mixshader.inputs[2], emission.outputs['Emission']);
            
            links.new(emission.inputs[0], tex_image.outputs['Color']);
            links.new(mix.inputs[1], tex_image.outputs['Alpha']);
            links.new(mat_output.inputs['Surface'], mixshader.outputs['Shader']);

    return material;


list_classes = [
    m7a_morph_panel,           mish_moprh_aspect_ratio,    m7a_morph_items,         m7a_morph_show_selected,
    m7a_morph_add_img_file,    m7a_morph_remove_img_file, m7a_morph_move_up_image, m7a_morph_move_down_image,
    m7a_morph_start,           m7a_morph_cancel,          m7a_morph_back,          m7a_morph_add_point,
    m7a_morph_remove_point,    m7a_morph_create_line,     m7a_morph_remove_line,   m7a_morph_preview,
    m7a_morph_create,          m7a_morph_edit,            m7a_morph_settings,      m7a_morph_apply_form,
    m7a_morph_settings_change, m7a_morph_btn, 
];

def register():
    bpy.utils.register_class(m7a_morph_list_file);   bpy.utils.register_class(m7a_morph_list);
    
    bpy.types.Scene.m7a_morph_x = int_prop(name = "X", default = 16);
    bpy.types.Scene.m7a_morph_y = int_prop(name = "Y", default = 9);
    bpy.types.Scene.m7a_morph_l = point_prop(type = m7a_morph_list);

    bpy.types.Scene.m7a_morph_ratio  = bool_prop(name = "Fixed Ratio",   default = True);
    bpy.types.Scene.m7a_morph_use_vrtx = bool_prop(name = "Use Image Vertex", default = True);
    bpy.types.Scene.m7a_morph_borders = bool_prop(name = "Fixed Borders", default = True);
    bpy.types.Scene.m7a_morph_loop = bool_prop(name = "Loop", default = False);
    bpy.types.Scene.m7a_morph_transparent = bool_prop(name = "Transparent Background", default = False);
    bpy.types.Scene.m7a_morph_index  = int_prop();

    bpy.types.Scene.m7a_morph_envelope  = float_prop (name = "Envelope Distance",    description = "Enter a point's envelope distance", default = 0.01,  min = 0.0, max = 100.0);
    bpy.types.Scene.m7a_morph_envelope_change  = float_prop (name = "Envelope Distance",    description = "Enter a point's envelope distance", default = 0.01,  min = 0.0, max = 100.0);
    bpy.types.Scene.m7a_morph_point_size  = float_prop (name = "Size",    description = "Enter a size point", default = 1.0,  min = 0, max = 100);
    bpy.types.Scene.m7a_morph_point_size_change = float_prop (name = "Size", description = "Enter a size point", default = 1.0,  min = 0, max = 100);
    bpy.types.Scene.m7a_morph_quality     = int_prop   (name = "Quality", description = "Enter a quality",    default = 100,   min = 1, max = 100);
    bpy.types.Scene.m7a_morph_subdevision = int_prop   (name = "Sub",     description = "Subdevision",        default = 1,    min = 0, max = 6);
    bpy.types.Scene.m7a_morph_opts        = enum_prop  (name = "Options", description = "Select Options",     default = "3d_cursor", items = morph_list_opts);
    bpy.types.Scene.m7a_morph_form        = enum_prop  (name = "Form",    description = "Select Form",        default = "dot",   items = morph_list_form);
    bpy.types.Scene.m7a_morph_form_change = enum_prop  (name = "Form",    description = "Select Form",        default = "dot",   items = morph_list_form);
    bpy.types.Scene.m7a_morph_method      = enum_prop  (name = "Method",  description = "Select Method",      default = "del",   items = morph_list_Method);
    bpy.types.Scene.m7a_morph_animate_by  = enum_prop  (name = "Animate By", description = "Select Method Conections", default = "envl", items = morph_list_animate_by);
        
    bpy.types.Scene.m7a_morph_color      = float_v_prop(name="Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0));
    bpy.types.Scene.m7a_morph_a_color    = float_v_prop(name="Active Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.0, 1.0, 0.0, 1.0));
        
    bpy.types.Scene.m7a_morph_preview    = float_prop (name = "Preview slider", default = 0.500,  min = 0.000, max = 1.000);

    [bpy.utils.register_class(cls) for cls in list_classes];

def unregister():
    bpy.utils.unregister_class(m7a_morph_list_file); bpy.utils.unregister_class(m7a_morph_list);

    del bpy.types.Scene.m7a_morph_x;
    del bpy.types.Scene.m7a_morph_y;
    del bpy.types.Scene.m7a_morph_l;
    del bpy.types.Scene.m7a_morph_ratio;
    del bpy.types.Scene.m7a_morph_use_vrtx;
    del bpy.types.Scene.m7a_morph_index;
    del bpy.types.Scene.m7a_morph_envelope;
    del bpy.types.Scene.m7a_morph_envelope_change;
    del bpy.types.Scene.m7a_morph_point_size;
    del bpy.types.Scene.m7a_morph_point_size_change;
    del bpy.types.Scene.m7a_morph_quality;
    del bpy.types.Scene.m7a_morph_subdevision;
    del bpy.types.Scene.m7a_morph_opts;
    del bpy.types.Scene.m7a_morph_form;
    del bpy.types.Scene.m7a_morph_form_change;
    del bpy.types.Scene.m7a_morph_method;
    del bpy.types.Scene.m7a_morph_borders;
    del bpy.types.Scene.m7a_morph_loop;
    del bpy.types.Scene.m7a_morph_transparent;
    del bpy.types.Scene.m7a_morph_color;
    del bpy.types.Scene.m7a_morph_a_color;
    del bpy.types.Scene.m7a_morph_preview;

    [bpy.utils.unregister_class(cls) for cls in list_classes];

if __name__ == "__main__": register();
