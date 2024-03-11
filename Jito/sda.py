# Traceback (most recent call last):
#   File "F:\___PROGRAMS\PYTHON\Solana\Jito\send_buy.py", line 181, in <module>
#     bb = send_bundle(client= client,rpc_url='https://rpc.shyft.to?api_key=ooAcuBUUvuKkflvP',
#          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "F:\___PROGRAMS\PYTHON\Solana\Jito\send_buy.py", line 167, in send_bundle
#     packets = [tx_to_protobuf_packet(tx) for tx in txs]
#               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "F:\___PROGRAMS\PYTHON\Solana\Jito\send_buy.py", line 167, in <listcomp>
#     packets = [tx_to_protobuf_packet(tx) for tx in txs]
#                ^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "F:\___PROGRAMS\PYTHON\Solana\mrroot\Lib\site-packages\jito_searcher_client\convert.py", line 24, in tx_to_protobuf_packet
#     data=tx.serialize(),
#          ^^^^^^^^^^^^
# AttributeError: 'solders.transaction.Transaction' object has no attribute 'serialize'