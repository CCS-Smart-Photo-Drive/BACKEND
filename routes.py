from flask import render_template, request, redirect, url_for
from app import app, db
from models import User, Event, Image
import cloudinary.uploader

