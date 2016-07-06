class DAGManJob(object):
    """DAGMan job

    Specify a DAG's input.

    Parameters
    ----------
    filename : str
        DAGMan input file
    nodes : List[DAGManNode]
        Sequence of DAGMan nodes

    """
    def __init__(self, filename, nodes):
        self.filename = filename
        self.nodes = nodes
        self._dependencies = {}
        self._written_to_disk = False

    def __str__(self):
        job = [str(node) for node in self.nodes]

        job.extend("PARENT {0} CHILD {1}".format(parents, children)
                   for parents, children in self.dependencies)

        return "\n".join(job)

    def dump(self):
        """Writes DAGMan input file to `filename`.

        """
        for node in self.nodes:
            if not isinstance(node.submit_description, str):
                node.submit_description.dump()

        with open(self.filename, "w") as ostream:
            ostream.write(str(self))

        self._written_to_disk = True

    def add_dependency(self, parents, children):
        """Add dependency within the DAG.

        Nodes are parents and/or children within the DAG. A parent node
        must be completed successfully before any of its children may be
        started. A child node may only be started once all its parents
        have successfully completed.

        Parameters
        ----------
        parents : Tuple[str]
            Parent node names
        children : Tuple[str]
            Children node names

        Raises
        ------
        ValueError
            If `parents` or `children` contains an unknown DAGMan node.

        """
        nodes = [node.name for node in self.nodes]

        if not all(node in nodes for node in parents):
            raise ValueError("Unknown DAGMan node.")

        if not all(node in nodes for node in children):
            raise ValueError("Unknown DAGMan node.")

        self._dependencies[parents] = children

    @property
    def dependencies(self):
        """Str: Dependencies within the DAG
        """
        return [(" ".join(parents), " ".join(children))
                for parents, children in self._dependencies.iteritems()]

    @property
    def written_to_disk(self):
        """Bool: If `True` DAGMan input file was written to disk.
        """
        return self._written_to_disk


class DAGManNode(object):
    """DAGMan node

    Specify a DAG's node.

    Attributes
    ----------
    name : str
        Uniquely identifies nodes within the DAGMan input file and in
        output messages.
    submit_description : HTCondorSubmit, str
        HTCondor submit description
    keywords : Dict[str, object]
        Mapping of objects describing node keywords

    """
    def __init__(self, name, submit_description, **kwargs):
        self.name = name
        self.submit_description = submit_description
        self.keywords = dict(kwargs)

    def __str__(self):
        if isinstance(self.submit_description, str):
            filename = self.submit_description
        else:
            filename = self.submit_description.filename

        node = ["JOB {job} {name}".format(job=self.name, name=filename)]

        node.extend("{key} {job} {value}".format(
            key=key, job=self.name, value=value)
            for key, value in self.keywords.iteritems())

        return "\n".join(node)


class DAGManScript(object):
    """Pre-processing or post-processing

    Specify a shell script/batch file to be executed either before a
    job within a node is submitted or after a job within a node
    completes its execution.

    Attributes
    ----------
    executable : str
        Specifies the shell script/batch file to be executed.
    arguments : List[object]
        Sequence of objects describing script/batch file arguments

    """
    def __init__(self, executable, *args):
        self.executable = executable
        self.arguments = list(args)

    def __str__(self):
        if len(self.arguments) > 0:
            arguments = " ".join("{0}".format(arg) for arg in self.arguments)
            return "{name} {args}".format(name=self.executable, args=arguments)
        else:
            return self.executable


class Macros(dict):
    r"""Define macros for DAGMan node.

    Derived from `dict`; only `__str__` is re-implemented to meet the
    DAGMan macro syntax.

    """
    def __str__(self):
        return " ".join('{key}="{val}"'.format(key=key, val=val)
                        for key, val in self.iteritems())