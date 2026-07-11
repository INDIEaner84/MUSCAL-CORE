import json
import os

from mcxf_fusion import store_mcxf


class ChatFolderCompiler:
    def __init__(self, mkc_compiler):
        self.mkc = mkc_compiler

    def load_folder(self, path):
        chats = []
        for file in os.listdir(path):
            if file.endswith(".txt"):
                with open(os.path.join(path, file), "r", encoding="utf-8") as f:
                    chats.append({
                        "file": file,
                        "content": f.read()
                    })
        return chats

    def compile_all(self, folder_path, auto_store=True):
        chats = self.load_folder(folder_path)
        mcxf_documents = []
        for chat in chats:
            mcxf = self.mkc(chat["content"])
            doc = {"source": chat["file"], "mcxf": mcxf}
            mcxf_documents.append(doc)
            if auto_store:
                store_mcxf(doc)
        return {
            "documents": mcxf_documents,
            "count": len(mcxf_documents)
        }
