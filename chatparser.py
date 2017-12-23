# -*- coding: utf-8 -*-
"""Parses WhatsApp conversation .txt files"""

import hashlib
import json
import re
from os import walk

from myexceptions import ParseError


class Digest(object):
    """Represents the structure of the digest.json file"""

    def __init__(self, fobj=None):
        if fobj is None:
            self.files = dict()
            self.conversations = []
        else:
            data = json.load(fobj)
            self.conversations = data["conversations"]
            self.files = data["files"]

    def add(self, fname, hashhex, conv):
        """Adds a parsed conversation file to the digest list"""
        self.files[fname] = hashhex
        self.conversations.append(conv)


def readchats(folder="./training_data/"):
    """Reads all example chats in the provided folder"""

    _, _, filenames = next(walk(folder), (None, None, []))
    if "digest.json" in filenames:
        filenames.remove("digest.json")

    def parseconversation(fname):
        """Parses .txt files as WhatsApp conversations"""
        statements = []
        header = re.compile(
            r'(\d{1,2}\/\d{1,2}\/\d{1,2}, \d?\d:\d?\d - .+?: )')
        try:
            conv = open(folder + fname)
            for line in conv:
                if "<Media omitted>" in line or "Messages to this chat and calls are now secured with end-to-end encryption." in line:
                    continue
                if header.match(line) is not None:
                    statements.append(header.sub('', line))
                else:
                    statements[-1] += line
        except Exception:
            raise ParseError
        finally:
            conv.close()
        return statements

    def gethash(fname):
        """Generates MD5 hash digest for a file"""
        hash_md5 = hashlib.md5()
        with open(folder + fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def gendigest():
        """Generates summary of all training conversations found"""
        digest = Digest()
        for f in filenames:
            check = gethash(f)
            conv = parseconversation(f)
            digest.add(f, check, conv)
        return digest

    def checkifvalid(old):
        """Checks if digest.json is up to date"""
        current = []
        for name in filenames:
            current.append(gethash(name))
        for f in old.files.values():
            if f not in current:
                return False
        return True

    try:
        with open(folder + "digest.json", 'r') as data:
            existing = Digest(data)
        if checkifvalid(existing) is True:
            return existing.conversations
        else:
            print("Digest is outdated, generating new one...")
    except Exception:
        print("Valid training digest not found! Generating new one...")

    dig = gendigest()

    with open(folder + "digest.json", 'w') as f:
        json.dump(dig.__dict__, f)
    return dig.conversations