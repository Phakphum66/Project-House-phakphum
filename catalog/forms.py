from __future__ import annotations

from django import forms

from designs.models import HouseDesign

from .models import CatalogDesign


class CatalogDesignForm(forms.ModelForm):
    class Meta:
        model = CatalogDesign
        fields = [
            "name",
            "concept",
            "base_price",
            "area_sqm",
            "bedrooms",
            "bathrooms",
            "dimensions",
            "cover_image",
            "floor_plan_image",
            "is_featured",
        ]
        widgets = {
            "concept": forms.Textarea(attrs={"rows": 5}),
            "dimensions": forms.TextInput(attrs={"placeholder": "เช่น 10 x 12 เมตร"}),
        }
        labels = {
            "name": "ชื่อแบบบ้าน",
            "concept": "คอนเซ็ปต์ / คำอธิบาย",
            "base_price": "ราคาเริ่มต้น",
            "area_sqm": "พื้นที่ใช้สอย (ตร.ม.)",
            "bedrooms": "จำนวนห้องนอน",
            "bathrooms": "จำนวนห้องน้ำ",
            "dimensions": "ขนาดอาคาร",
            "cover_image": "ภาพหน้าปก",
            "floor_plan_image": "ผังพื้น",
            "is_featured": "แนะนำโดยทีมงาน",
        }
        help_texts = {
            "cover_image": "อัปโหลดภาพหน้าปกที่ชัดเจน (สัดส่วน 4:3 แนะนำ)",
            "floor_plan_image": "ถ้ามี ให้แนบไฟล์ผังพื้นหรือแบบผัง",
        }

    def __init__(self, *args, **kwargs):
        source_design: HouseDesign | None = kwargs.pop("source_design", None)
        super().__init__(*args, **kwargs)

        if source_design and not self.is_bound:
            self.initial.setdefault("name", source_design.title)
            self.initial.setdefault("concept", source_design.description)

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "form-control")
            else:
                widget.attrs.setdefault("class", "form-control")

        numeric_attrs = {
            "base_price": {"min": "0", "step": "1000"},
            "area_sqm": {"min": "0", "step": "1"},
            "bedrooms": {"min": "0", "step": "1"},
            "bathrooms": {"min": "0", "step": "1"},
        }
        for field_name, attrs in numeric_attrs.items():
            self.fields[field_name].widget.attrs.update(attrs)

        self.fields["is_featured"].widget.attrs.setdefault("role", "switch")
