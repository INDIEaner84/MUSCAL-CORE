class TripleExtractor:
    def extract(self, text):
        triples = []

        sentences = text.split(".")

        for s in sentences:
            s = s.strip().lower()

            if "is" in s:
                parts = s.split("is")
                if len(parts) == 2:
                    triples.append((parts[0].strip(), "is", parts[1].strip()))

            if "has" in s:
                parts = s.split("has")
                if len(parts) == 2:
                    triples.append((parts[0].strip(), "has", parts[1].strip()))

        return triples
