from rest_framework import serializers
from .models import Problem, CrawlerSource, TestCase

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'oj_display_id', 'title']

class CrawlerSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlerSource
        fields = ['id', 'name']

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ['id', 'content', 'created_at']