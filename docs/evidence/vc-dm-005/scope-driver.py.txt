"""SVG 交换必须披露实际图像元素范围，不能从扩展名或路径数量推断无损。"""
import base64
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]
def png():
    def chunk(name,data):
        return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\xff\0\0\xff'))+chunk(b'IEND',b'')
def module():
    spec=importlib.util.spec_from_file_location('scope_loss',ROOT/'skills/vectorcraft-use/scripts/exchange_loss.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
class SvgRasterScopeTests(unittest.TestCase):
    def test_embedded_raster_geometry_and_ancestor_transforms_disclosed(self):
        data=png();xml=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g transform="translate(10 20)"><image id="blurred" x="2" y="3" width="4" height="5" href="data:image/png;base64,'+base64.b64encode(data).decode()+'"/></g></svg>')
        value=module().svg_image_scope(xml)
        self.assertFalse(value['vectorOnly']);self.assertFalse(value['losslessVectorClaimAllowed'])
        row=value['elements'][0]
        self.assertEqual(row['classification'],'embedded-raster');self.assertEqual(row['payloadSha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(row['geometry'],{'x':'2','y':'3','width':'4','height':'5'})
        self.assertEqual(row['ancestorTransforms'],['translate(10 20)']);self.assertFalse(value['completePaintBounds'])
    def test_linked_unknown_resource_not_fetched_or_claimed_raster(self):
        uri='https://invalid.example/secret.png';value=module().svg_image_scope(ET.fromstring('<svg><image href="'+uri+'"/></svg>'))
        self.assertFalse(value['vectorOnly']);self.assertEqual(value['elements'][0]['classification'],'unresolved-reference')
        self.assertNotIn(uri,str(value));self.assertFalse(value['losslessVectorClaimAllowed'])
    def test_embedded_svg_is_not_misclassified_as_raster(self):
        data=base64.b64encode(b'<svg><path d="M0 0L1 1"/></svg>').decode()
        value=module().svg_image_scope(ET.fromstring('<svg><image href="data:image/svg+xml;base64,'+data+'"/></svg>'))
        self.assertEqual(value['elements'][0]['classification'],'embedded-vector-reference');self.assertFalse(value['vectorOnly'])
    def test_filter_without_image_does_not_establish_rasterization(self):
        value=module().svg_image_scope(ET.fromstring('<svg><defs><filter><feGaussianBlur/></filter></defs><path/></svg>'))
        self.assertEqual(value['elements'],[]);self.assertTrue(value['vectorOnly']);self.assertFalse(value['losslessVectorClaimAllowed'])
    def test_invalid_base64_rejected(self):
        with self.assertRaisesRegex(ValueError,'loss_svg_image_data_invalid'):
            module().svg_image_scope(ET.fromstring('<svg><image href="data:image/png;base64,%%%"/></svg>'))

if __name__=='__main__':unittest.main()
